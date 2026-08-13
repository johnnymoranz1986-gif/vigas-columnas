import math
import os
import telebot

TOKEN = "TU_TOKEN_AQUI"  # O tu os.getenv si prefieres variable de entorno
bot = telebot.TeleBot(TOKEN)

class MaterialesMKS:
    def __init__(self, f_c_kgcm2, f_y_kgcm2):
        # Convertimos kg/cm2 a MPa internamente para las fórmulas normalizadas del ACI
        # 1 MPa ≈ 10.197 kg/cm2  ->  kg/cm2 / 10.197 = MPa
        self.f_c_kgcm2 = f_c_kgcm2
        self.f_y_kgcm2 = f_y_kgcm2
        self.f_c = f_c_kgcm2 / 10.197  
        self.f_y = f_y_kgcm2 / 10.197  

class VigaRectangularMKS:
    def __init__(self, b_m, h_m, rec_cm, materiales):
        self.b = b_m  # Ancho en metros
        self.h = h_m  # Peralte total en metros
        self.d = self.h - (rec_cm / 100.0)  # Peralte efectivo en metros
        self.mat = materiales
        self.phi_flexion = 0.9
        self.phi_corte = 0.75

    def calcular_refuerzo_flexion(self, M_u_tm):
        # M_u_tm en Toneladas-Metro -> Convertir a N*m (1 t*m = 9806.65 N*m)
        M_u_Nm = M_u_tm * 9806.65
        
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
            
        # Área de acero en cm² (b y d están en metros, pasamos a cm multiplicando por 10000)
        A_s_req = rho_final * self.b * self.d * 10000.0

        return {
            "Momento Último": f"{M_u_tm} t·m",
            "Tipo de Refuerzo": tipo,
            "Área de Acero (As)": f"{round(A_s_req, 2)} cm²",
            "Acero Mínimo": f"{round(rho_min * self.b * self.d * 10000.0, 2)} cm²"
        }

    def calcular_refuerzo_corte(self, V_u_t):
        # V_u_t en Toneladas -> Convertir a Newtons (1 t = 9806.65 N)
        V_u_N = V_u_t * 9806.65
        
        # b y d en metros -> pasarlos a mm para la fórmula de corte (b*1000, d*1000)
        V_c_N = 0.17 * math.sqrt(self.mat.f_c) * (self.b * 1000.0) * (self.d * 1000.0)
        V_s_req_N = (V_u_N / self.phi_corte) - V_c_N
        
        resumen = {
            "Cortante Último (Vu)": f"{V_u_t} t",
            "Cortante Concreto (Vc)": f"{round(V_c_N / 9806.65, 2)} t",
        }
        
        if V_s_req_N <= 0:
            resumen["Estado Corte"] = "Estribos mínimos requeridos por norma"
        else:
            resumen["Estado Corte"] = f"Requiere diseño de estribos (Vs = {round(V_s_req_N / 9806.65, 2)} t)"

        return resumen

@bot.message_handler(commands=['start', 'help'])
def enviar_bienvenida(message):
    texto = (
        "📐 **BOT DE DISEÑO ESTRUCTURAL (MKS)** 📐\n\n"
        "Unidades MKS:\n"
        "• **b, h:** en metros (m)\n"
        "• **Recubrimiento:** en centímetros (cm)\n"
        "• **f'c, fy:** en kg/cm²\n"
        "• **Momento (Mu):** en t·m\n"
        "• **Cortante (Vu):** en t\n\n"
        "**Formato de uso:**\n"
        "/viga [b] [h] [rec] [fc] [fy] [Mu] [Vu]\n\n"
        "**Ejemplo:**\n"
        "/viga 0.30 0.50 4 210 4200 12.5 8.0"
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

@bot.message_handler(commands=['viga'])
def diseñar_viga_comando(message):
    try:
        partes = message.text.split()
        if len(partes) < 8:
            bot.reply_to(message, "⚠️ Faltan datos. Escribe todo junto en un solo mensaje:\n/viga 0.30 0.50 4 210 4200 12.5 8.0")
            return

        b = float(partes[1])
        h = float(partes[2])
        rec = float(partes[3])
        fc = float(partes[4])
        fy = float(partes[5])
        mu = float(partes[6])
        vu = float(partes[7])

        mat = MaterialesMKS(f_c_kgcm2=fc, f_y_kgcm2=fy)
        viga = VigaRectangularMKS(b_m=b, h_m=h, rec_cm=rec, materiales=mat)
        
        res_flexion = viga.calcular_refuerzo_flexion(M_u_tm=mu)
        res_corte = viga.calcular_refuerzo_corte(V_u_t=vu)

        respuesta = "📊 **RESULTADOS DE DISEÑO (MKS)** 📊\n\n"
        respuesta += "🔹 **Flexión:**\n"
        for k, v in res_flexion.items():
            respuesta += f"• {k}: {v}\n"
            
        respuesta += "\n🔸 **Corte:**\n"
        for k, v in res_corte.items():
            respuesta += f"• {k}: {v}\n"

        bot.reply_to(message, respuesta, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Error en los datos ingresados. Asegúrate de usar puntos decimales (ej: 0.30).\nDetalle: {str(e)}")

if __name__ == "__main__":
    bot.infinity_polling()
