import math
import os
import telebot
from telebot import types

# Configuración del Bot (Asegúrate de poner tu token real o usar variables de entorno)
TOKEN = os.getenv("8978402989:AAFKlKtf_Aa-qyeyNa1lw3T8sJkLzpDKK4Y")
bot = telebot.TeleBot(TOKEN)

class Materiales:
    def __init__(self, f_c_mpa, f_y_mpa, E_s_gpa=200):
        self.f_c = f_c_mpa  # Concreto (MPa)
        self.f_y = f_y_mpa  # Acero (MPa)
        self.E_s = E_s_gpa * 1000

class VigaRectangular:
    def __init__(self, b_mm, h_mm, recubrimiento_mm, materiales):
        self.b = b_mm / 1000.0  # (m)
        self.h = h_mm / 1000.0  # (m)
        self.d = self.h - (recubrimiento_mm / 1000.0)  # (m)
        self.mat = materiales
        self.phi_flexion = 0.9
        self.phi_corte = 0.75

    def calcular_refuerzo_flexion(self, M_u_kNm):
        M_u_Nm = M_u_kNm * 1000.0
        rho_min = max(0.25 * math.sqrt(self.mat.f_c) / self.mat.f_y, 1.4 / self.mat.f_y)
        rho_max = 0.85 * self.mat.f_c / self.mat.f_y * (600 / (600 + self.mat.f_y))
        
        R = M_u_Nm / (self.phi_flexion * self.b * (self.d**2))
        m = self.mat.f_y / (0.85 * self.mat.f_c)
        
        try:
            delta = 1.0 - (2.354 * R / self.mat.f_c)
            rho_requerido = (1.0 - math.sqrt(max(0, delta))) / m
        except ZeroDivisionError:
            rho_requerido = 0

        if rho_requerido < rho_min:
            tipo = "Simple reforzada (Refuerzo mínimo)"
            rho_final = rho_min
        elif rho_requerido <= rho_max:
            tipo = "Simple reforzada"
            rho_final = rho_requerido
        else:
            tipo = "Doblemente reforzada"
            rho_final = rho_max
            
        A_s_req = rho_final * self.b * self.d * 1000.0**2

        return {
            "Momento Último": f"{M_u_kNm} kN*m",
            "Tipo de Refuerzo": tipo,
            "Área de Acero (As)": f"{round(A_s_req, 2)} mm²",
            "Acero Mínimo": f"{round(rho_min * self.b * self.d * 1000.0**2, 2)} mm²"
        }

    def calcular_refuerzo_corte(self, V_u_kN):
        V_u_N = V_u_kN * 1000.0
        V_c_N = 0.17 * math.sqrt(self.mat.f_c) * (self.b * 1000.0) * (self.d * 1000.0)
        V_s_req_N = (V_u_N / self.phi_corte) - V_c_N
        
        resumen = {
            "Cortante Último (Vu)": f"{V_u_kN} kN",
            "Cortante Concreto (Vc)": f"{round(V_c_N / 1000.0, 2)} kN",
        }
        
        if V_s_req_N <= 0:
            resumen["Estado Corte"] = "Estribos mínimos requeridos por norma"
        else:
            resumen["Estado Corte"] = f"Requiere diseño de estribos (Vs = {round(V_s_req_N / 1000.0, 2)} kN)"

        return resumen

# --- Comandos del Bot ---

@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    texto = (
        "¡Hola! Soy tu bot de diseño estructural (Norma ACI / RNE).\n\n"
        "Comandos disponibles:\n"
        "/viga [b_mm] [h_mm] [rec_mm] [fc] [fy] [Mu_kNm] [Vu_kN]\n\n"
        "Ejemplo:\n"
        "/viga 300 500 60 28 420 250 150"
    )
    bot.reply_to(message, texto)

@bot.message_handler(commands=['viga'])
def diseñar_viga_comando(message):
    try:
        partes = message.text.split()
        if len(partes) < 8:
            bot.reply_to(message, "Faltan datos. Usa el formato:\n/viga b h rec fc fy Mu Vu\nEjemplo: /viga 300 500 60 28 420 250 150")
            return

        b = float(partes[1])
        h = float(partes[2])
        rec = float(partes[3])
        fc = float(partes[4])
        fy = float(partes[5])
        mu = float(partes[6])
        vu = float(partes[7])

        # Procesar cálculo
        mat = Materiales(f_c_mpa=fc, f_y_mpa=fy)
        viga = VigaRectangular(b_mm=b, h_mm=h, recubrimiento_mm=rec, materiales=mat)
        
        res_flexion = viga.calcular_refuerzo_flexion(M_u_kNm=mu)
        res_corte = viga.calcular_refuerzo_corte(V_u_kN=vu)

        # Construir respuesta
        respuesta = "📊 **RESULTADOS DE DISEÑO DE VIGA** 📊\n\n"
        respuesta += "🔹 **Flexión:**\n"
        for k, v in res_flexion.items():
            respuesta += f"• {k}: {v}\n"
            
        respuesta += "\n🔸 **Corte:**\n"
        for k, v in res_corte.items():
            respuesta += f"• {k}: {v}\n"

        bot.reply_to(message, respuesta, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"Hubo un error al procesar los datos. Revisa los valores numéricos.\nDetalle: {str(e)}")

# Mantener el bot ejecutándose de manera continua
if __name__ == "__main__":
    print("Bot iniciado correctamente y escuchando...")
    bot.infinity_polling()
