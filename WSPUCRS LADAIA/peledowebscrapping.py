import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
import re

# Configuração do Selenium
def iniciar_navegador(url):
    service = Service()  # Adicione o caminho do ChromeDriver se necessário
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    return driver

# A função coletar_nomes permanece inalterada
def coletar_nomes(driver, url, curso_desejado):
    driver.get(url)
    time.sleep(2)
    nomes = []
    for letra in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        try:
            lista_letras = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "classificados-indice"))
            )
            botao_letra = lista_letras.find_element(By.XPATH, f"//a[text()='{letra}']")
            botao_letra.click()
            time.sleep(2)
            elementos = driver.find_elements(By.XPATH, f"//nav[@id='{letra.lower()}']//li[@class='classificados-infos']")
            for elemento in elementos:
                try:
                    colocacao_do_candidato = elemento.find_element(By.CSS_SELECTOR, ".classificado-posicao.col-sm-2").text.strip()
                    nome_do_candidato = elemento.find_element(By.CSS_SELECTOR, ".classificado-nome.col-sm-5").text.strip()
                    curso_e_metodo = elemento.find_elements(By.CSS_SELECTOR, ".classificado-curso.col-sm-2")
                    
                    curso = curso_e_metodo[0].text.strip() if len(curso_e_metodo) > 0 else "N/A"
                    metodo_de_classificacao = curso_e_metodo[1].text.strip() if len(curso_e_metodo) > 1 else "N/A"
                    
                    if curso == curso_desejado:
                        nomes.append(f"{nome_do_candidato} passou em {colocacao_do_candidato}º lugar e foi {metodo_de_classificacao}")
                except Exception as e:
                    print(f"Erro ao processar candidato: {e}")
        except Exception as e:
            print(f"Erro ao acessar a letra '{letra}': {e}")
    return nomes

# Classe para gerenciar a interface gráfica
class App:
    def __init__(self):
        self.janela = tk.Tk()
        self.janela.title("Consulta de Aprovados")
        self.janela.geometry("800x600")
        self.janela.attributes("-fullscreen", True)
        self.janela.bind("<Escape>", lambda e: self.sair_tela_cheia())

        self.curso_desejado = tk.StringVar()
        self.ordem = tk.StringVar(value="alfabetica")  # Padrão para exibição
        self.resultados = []

        # Criar container principal
        self.container_principal = ttk.Frame(self.janela, padding="20")
        self.container_principal.pack(fill=tk.BOTH, expand=True)

        # Configurar telas
        self.tela_inicio()
        self.tela_ordem()
        self.tela_progresso()
        self.tela_resultados()

        # Mostrar a primeira tela
        self.frame_inicio.pack(fill=tk.BOTH, expand=True)

    def sair_tela_cheia(self):
        self.janela.attributes("-fullscreen", False)
        self.janela.geometry("1024x768")

    def tela_inicio(self):
        """Configura a tela inicial."""
        self.frame_inicio = ttk.Frame(self.container_principal)
        ttk.Label(self.frame_inicio, text="Consulta de Aprovados", font=("Arial", 36, "bold")).pack(pady=50)
        ttk.Label(self.frame_inicio, text="Digite o código do curso:", font=("Arial", 18)).pack(pady=10)
        ttk.Entry(self.frame_inicio, textvariable=self.curso_desejado, font=("Arial", 16), width=30).pack(pady=20)
        ttk.Button(self.frame_inicio, text="Consultar", command=self.perguntar_ordem, width=15).pack(pady=40)

    def tela_ordem(self):
        """Configura a tela para escolher a ordem de exibição."""
        self.frame_ordem = ttk.Frame(self.container_principal)
        ttk.Label(self.frame_ordem, text="Como gostaria de exibir os nomes?", font=("Arial", 24, "bold")).pack(pady=50)
        ttk.Button(self.frame_ordem, text="Alfabética", command=lambda: self.iniciar_coleta("alfabetica"), width=20).pack(pady=20)
        ttk.Button(self.frame_ordem, text="Por classificação", command=lambda: self.iniciar_coleta("classificacao"), width=20).pack(pady=20)

    def tela_progresso(self):
        """Configura a tela de progresso."""
        self.frame_progresso = ttk.Frame(self.container_principal)
        ttk.Label(self.frame_progresso, text="Coletando dados, por favor aguarde...", font=("Arial", 24)).pack(pady=50)
        self.barra_progresso = ttk.Progressbar(self.frame_progresso, mode='indeterminate', length=400)
        self.barra_progresso.pack(pady=20)

    def tela_resultados(self):
        """Configura a tela de resultados."""
        self.frame_resultados = ttk.Frame(self.container_principal)
        ttk.Label(self.frame_resultados, text="Resultados:", font=("Arial", 28, "bold")).pack(pady=30)
        self.lista_nomes = tk.Listbox(self.frame_resultados, font=("Arial", 14), width=80, height=25)
        self.lista_nomes.pack(pady=10)
        ttk.Button(self.frame_resultados, text="Fechar", command=self.janela.destroy, width=15).pack(pady=20)

    def perguntar_ordem(self):
        """Mostra a tela para escolher a ordem."""
        self.frame_inicio.pack_forget()
        self.frame_ordem.pack(fill=tk.BOTH, expand=True)

    def iniciar_coleta(self, ordem):
        """Inicia a coleta de dados."""
        self.ordem.set(ordem)
        curso = self.curso_desejado.get()
        if not curso:
            messagebox.showwarning("Entrada inválida", "Por favor, digite o código do curso.")
            return

        self.frame_ordem.pack_forget()
        self.frame_progresso.pack(fill=tk.BOTH, expand=True)
        self.barra_progresso.start(10)

        threading.Thread(target=self.coletar_dados, args=(curso,)).start()

    def coletar_dados(self, curso):
        """Coleta os dados e atualiza a interface."""
        url = "https://listao.pucrs.br/2025/2024_11_28-vestibular_verao_2025-00-oc_10-demais_cursos-prova_23_nov-1a_chamada-classificados.php"
        driver = iniciar_navegador(url)
        self.resultados = coletar_nomes(driver, url, curso)
        driver.quit()

        if self.ordem.get() == "classificacao":
            self.resultados.sort(key=lambda x: int(re.search(r"(\d+)", x).group(1)))

        self.janela.after(0, self.mostrar_resultados)

    def mostrar_resultados(self):
        """Exibe os resultados na tela."""
        self.frame_progresso.pack_forget()
        self.frame_resultados.pack(fill=tk.BOTH, expand=True)
        self.barra_progresso.stop()

        if not self.resultados:
            messagebox.showinfo("Sem resultados", "Nenhum candidato encontrado para o curso especificado.")
        else:
            for nome in self.resultados:
                self.lista_nomes.insert(tk.END, nome)

# Função principal
def main():
    app = App()
    app.janela.mainloop()

if __name__ == "__main__":
    main()
