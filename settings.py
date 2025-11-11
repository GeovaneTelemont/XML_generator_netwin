import os, time
from constants import SECRET_KEY, MAX_CONTENT_LENGTH, UPLOAD_FOLDER, DOWNLOAD_FOLDER 

class Config:
    def __init__(self):
        self.secret_key = SECRET_KEY
        self.max_content_lenght = MAX_CONTENT_LENGTH
        self.upload_folder = UPLOAD_FOLDER
        self.download_folder = DOWNLOAD_FOLDER
        self.create_folder_download(self.download_folder)
        self.limpar_arquivos_antigos()

    def create_folder_download(self, download_folder):
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

    def config_init(self, app):
        app.config["SECRET_KEY"] = self.secret_key
        app.config["UPLOAD_FOLDER"] = self.upload_folder
        app.config["MAX_CONTENT_LENGTH"] = self.max_content_lenght
        app.config["DOWNLOAD_FOLDER"] = self.download_folder

        

    def limpar_arquivos_antigos(self):
        """Limpa arquivos com mais de 1 hora na pasta de downloads"""
        try:
            print("limpando arquivos antigos")
            agora = time.time()
            for filename in os.listdir(self.download_folder):
                file_path = os.path.join(self.download_folder, filename)
                if os.path.isfile(file_path):
                    # Verificar se o arquivo tem mais de 1 hora
                    if agora - os.path.getctime(file_path) > 500:
                        os.remove(file_path)
        except Exception as e:
            print(f"Erro ao limpar arquivos antigos: {e}")

