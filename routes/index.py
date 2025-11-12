from flask import (
    Blueprint,
    Response,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_file,
    session,
    jsonify,
)
from werkzeug.utils import secure_filename
from settings import Config
from service.service_xml_generator import processar_csv
from service.service_convert_csv_paterns import (
    validar_colunas_csv,
    update_progress,
    processar_csv_conversor,
    processar_csv_conversor_grande,
)
from constants import (
    ERRO_COMPLEMENTO2,
    ERRO_COMPLEMENTO3,
    LOG_COMPLEMENTOS,
    RESULTS_LOCK,
    MENSSAGE_QUEUE,
    PROCESSING_RESULTS,
)
import os, threading, queue, json

index_bp = Blueprint("index", __name__)

config = Config()


@index_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Nenhum arquivo selecionado")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Nenhum arquivo selecionado")
            return redirect(request.url)

        if file and file.filename.endswith(".csv"):
            filename = secure_filename(file.filename)
            filepath = os.path.join(config.upload_folder, filename)
            file.save(filepath)

            try:
                zip_filename, total_registros, log = processar_csv(filepath)
                flash(
                    f"Processamento concluído! {total_registros} registros processados."
                )

                if ERRO_COMPLEMENTO2 or ERRO_COMPLEMENTO3:
                    alert_type = "danger"
                else:
                    alert_type = "info"

                return render_template(
                    "resultado.html",
                    complementos=LOG_COMPLEMENTOS,
                    alert_type=alert_type,
                    log=log,
                    total_registros=total_registros,
                    zip_filename=zip_filename,
                )

            except Exception as e:
                flash(f"Erro no processamento: {str(e)}")
                return redirect(request.url)

            finally:
                # Limpar arquivo temporário
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            flash("Por favor, selecione um arquivo CSV")
            return redirect(request.url)

    return render_template("index.html")


@index_bp.route("/download/<filename>")
def download_file(filename):
    try:
        file_path = os.path.join(config.download_folder, filename)

        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            flash("Arquivo não encontrado")
            return redirect(url_for("index"))

        # Enviar o arquivo para download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="application/zip",
        )

    except Exception as e:
        flash(f"Erro ao fazer download: {str(e)}")
        return redirect(url_for("index"))


@index_bp.route("/sobre")
def sobre():
    return render_template("sobre.html")


@index_bp.route("/download-modelo-csv")
def download_modelo_csv():
    modelo_path = os.path.join(os.path.dirname(__file__), "csv_modelo", "modelo.csv")
    if not os.path.exists(modelo_path):
        flash("Arquivo modelo não encontrado.")
        return redirect(url_for("index"))
    return send_file(
        modelo_path,
        as_attachment=True,
        download_name="modelo.csv",
        mimetype="text/csv",
    )


# ========== NOVAS ROTAS COM PROGRESSO ==========


@index_bp.route("/progress")
def progress():
    """Rota para SSE do progresso - CORRIGIDA"""

    def generate():
        try:
            # Envia um ping inicial para manter a conexão
            yield f"data: {json.dumps({'message': 'Conectado...', 'status': 'connected'})}\n\n"

            last_data = None
            while True:
                try:
                    # Pega a mensagem mais recente da fila (com timeout)
                    data = MENSSAGE_QUEUE.get(timeout=30)

                    # Só envia se os dados mudaram
                    if data != last_data:
                        yield f"data: {json.dumps(data)}\n\n"
                        last_data = data

                        # Se o processamento terminou, encerra a conexão
                        if data.get("status") in ["completed", "error"]:
                            break

                    MENSSAGE_QUEUE.task_done()

                except queue.Empty:
                    # Timeout - envia ping para manter conexão
                    yield f"data: {json.dumps({'message': 'Aguardando...', 'status': 'waiting'})}\n\n"

        except GeneratorExit:
            # Cliente desconectou
            print("Cliente desconectou do SSE")
        except Exception as e:
            print(f"Erro no SSE: {e}")
            yield f"data: {json.dumps({'message': f'Erro: {str(e)}', 'status': 'error'})}\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@index_bp.route("/validar-csv", methods=["POST"])
def validar_csv():
    """Rota para validar o arquivo CSV via AJAX"""
    if "file" not in request.files:
        return jsonify({"valido": False, "erro": "Nenhum arquivo enviado"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"valido": False, "erro": "Nenhum arquivo selecionado"})

    if file and file.filename.endswith(".csv"):
        try:
            # Salva o arquivo temporariamente
            filename = secure_filename(file.filename)
            filepath = os.path.join(config.upload_folder, f"temp_{filename}")
            file.save(filepath)

            # Valida as colunas
            resultado_validacao = validar_colunas_csv(filepath)

            # Limpa o arquivo temporário
            if os.path.exists(filepath):
                os.remove(filepath)

            return jsonify(resultado_validacao)

        except Exception as e:
            # Limpa o arquivo temporário em caso de erro
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({"valido": False, "erro": f"Erro na validação: {str(e)}"})

    return jsonify({"valido": False, "erro": "Arquivo inválido"})


@index_bp.route("/conversor-csv", methods=["GET", "POST"])
def conversor_csv():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Nenhum arquivo selecionado")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Nenhum arquivo selecionado")
            return redirect(request.url)

        if file and file.filename.endswith(".csv"):
            filename = secure_filename(file.filename)
            filepath = os.path.join(config.upload_folder, filename)
            file.save(filepath)

            # Valida o arquivo antes de processar
            validacao = validar_colunas_csv(filepath)
            if not validacao["valido"]:
                colunas_faltantes = ", ".join(validacao["colunas_faltantes"])
                flash(f"❌ Arquivo inválido! Colunas faltantes: {colunas_faltantes}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

            # Reset progress data
            update_progress(
                "🕒 Iniciando processamento...",
                progress=0,
                current=0,
                total=0,
                status="processing",
            )

            try:
                # Verificar tamanho do arquivo
                file_size = os.path.getsize(filepath) / (1024 * 1024)

                # Limpar a fila de mensagens antigas
                while not MENSSAGE_QUEUE.empty():
                    try:
                        MENSSAGE_QUEUE.get_nowait()
                        MENSSAGE_QUEUE.task_done()
                    except queue.Empty:
                        break

                # Gerar um ID único para este processamento
                import uuid

                process_id = str(uuid.uuid4())

                # Iniciar processamento em thread separada
                def processar_arquivo(process_id, filepath, file_size):
                    try:
                        update_progress(
                            f"📊 Arquivo validado: {file_size:.2f} MB",
                            progress=5,
                        )

                        if file_size > 100:
                            update_progress(
                                "🔧 Usando processamento otimizado para arquivo grande...",
                                progress=10,
                            )
                            (
                                zip_filename,
                                total_registros,
                            ) = processar_csv_conversor_grande(filepath)
                        else:
                            update_progress("🔧 Processando arquivo...", progress=10)
                            (
                                zip_filename,
                                total_registros,
                            ) = processar_csv_conversor(filepath)

                        # Armazenar resultado no dicionário global
                        with RESULTS_LOCK:
                            PROCESSING_RESULTS[process_id] = {
                                "filename": zip_filename,
                                "total_registros": total_registros,
                                "status": "success",
                            }

                        update_progress(
                            "✅ Processamento concluído com sucesso!",
                            progress=100,
                            status="completed",
                        )

                    except Exception as e:
                        error_msg = f"❌ Erro no processamento: {str(e)}"
                        print(error_msg)

                        # Armazenar erro no dicionário global
                        with RESULTS_LOCK:
                            PROCESSING_RESULTS[process_id] = {
                                "error": str(e),
                                "status": "error",
                            }

                        update_progress(error_msg, status="error")
                    finally:
                        # Limpar arquivo temporário
                        if os.path.exists(filepath):
                            os.remove(filepath)

                thread = threading.Thread(
                    target=processar_arquivo,
                    args=(process_id, filepath, file_size),
                )
                thread.daemon = True
                thread.start()

                # Armazenar o process_id na session para recuperar depois
                session["current_process_id"] = process_id

                return redirect(url_for("index.progress_page"))

            except Exception as e:
                flash(f"❌ Erro ao iniciar processamento: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)
        else:
            flash("Por favor, selecione um arquivo CSV")
            return redirect(request.url)

    return render_template("conversor_csv.html")


@index_bp.route("/progress-page")
def progress_page():
    """Página que mostra o progresso"""
    return render_template("progresso.html")


@index_bp.route("/conversor-result")
def conversor_result():
    """Página de resultado após processamento"""
    process_id = session.get("current_process_id")

    if not process_id:
        flash("Nenhum processamento em andamento")
        return redirect(url_for("index.conversor_csv"))

    with RESULTS_LOCK:
        result = PROCESSING_RESULTS.get(process_id)

    if not result:
        flash(
            "Resultado não encontrado. O processamento pode ainda estar em andamento."
        )
        return redirect(url_for("index.conversor_csv"))

    if result.get("status") == "success":
        # Limpar o resultado após usar
        with RESULTS_LOCK:
            PROCESSING_RESULTS.pop(process_id, None)
        session.pop("current_process_id", None)

        return render_template(
            "resultado_conversor.html",
            total_registros=result["total_registros"],
            zip_filename=result["filename"],
        )

    elif result.get("status") == "error":
        error_msg = result.get("error", "Erro desconhecido")
        # Limpar o resultado após usar
        with RESULTS_LOCK:
            PROCESSING_RESULTS.pop(process_id, None)
        session.pop("current_process_id", None)

        flash(f"❌ Erro na conversão: {error_msg}")
        return redirect(url_for("index.conversor_csv"))

    else:
        flash("Processamento ainda em andamento...")
        return redirect(url_for("progress_page"))


@index_bp.route("/download-convertido/<filename>")
def download_convertido(filename):
    try:
        file_path = os.path.join(config.download_folder, filename)

        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            flash("Arquivo não encontrado")
            return redirect(url_for("index.conversor_csv"))

        # Enviar o arquivo para download
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype="text/csv",
        )

    except Exception as e:
        flash(f"Erro ao fazer download: {str(e)}")
        return redirect(url_for("conversor_csv"))


# Adicionar tratamento de erro para arquivos grandes
@index_bp.errorhandler(413)
def too_large(e):
    flash("O arquivo é muito grande. O tamanho máximo permitido é 2GB.")
    return redirect(request.url)
