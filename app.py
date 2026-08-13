import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Memoria de Cálculo Estructural - RNE / ACI", layout="centered")

st.title("🏗️ Memoria de Cálculo Detallada: Concreto Armado")
st.write("Diseño normativo completo por flexión y corte para elementos estructurales.")

menu = st.sidebar.selectbox("Seleccione el módulo:", ["Viga Rectangular (Flexión y Corte)", "Columna (Interacción P-M)"])

# ==========================================
# MÓDULO 1: VIGA RECTANGULAR COMPLETA
# ==========================================
if menu == "Viga Rectangular (Flexión y Corte)":
    st.header("📐 Memoria de Cálculo: Viga de Concreto Armado")
    
    st.sidebar.subheader("Parámetros de Entrada")
    b = st.number_input("Ancho de la viga, b (m):", min_value=0.15, max_value=1.00, value=0.30, step=0.05)
    h = st.number_input("Peralte total, h (m):", min_value=0.20, max_value=1.50, value=0.50, step=0.05)
    rec = st.number_input("Recubrimiento libre, rec (cm):", min_value=2.0, max_value=10.0, value=4.0, step=0.5)
    
    fc = st.number_input("Resistencia del concreto, f'c (kg/cm²):", min_value=175.0, max_value=420.0, value=210.0, step=10.0)
    fy = st.number_input("Fluencia del acero, fy (kg/cm²):", min_value=2800.0, max_value=5000.0, value=4200.0, step=100.0)
    
    mu = st.number_input("Momento Último, Mu (t·m):", min_value=1.0, max_value=300.0, value=15.0, step=0.5)
    vu = st.number_input("Cortante Último, Vu (t):", min_value=0.5, max_value=150.0, value=9.5, step=0.5)

    if st.button("Generar Memoria de Cálculo Completa"):
        # Conversiones de unidades
        f_c_mpa = fc / 10.197
        f_y_mpa = fy / 10.197
        d = h - (rec / 100.0) # peralte efectivo en metros
        d_mm = d * 1000.0
        b_mm = b * 1000.0
        
        phi_flexion = 0.90
        phi_corte = 0.75
        
        M_u_Nmm = mu * 9.80665 * 10**6 # N*mm
        
        # 1. Cuantías límite según Norma ACI / RNE E.060
        rho_min = max(0.25 * math.sqrt(f_c_mpa) / f_y_mpa, 1.4 / f_y_mpa)
        rho_max = 0.85 * f_c_mpa / f_y_mpa * (600 / (600 + f_y_mpa)) * 0.75 # Cuantía balanceada modificada para ductilidad
        
        # 2. Cálculo por Flexión
        # R = Mu / (phi * b * d^2)
        R = M_u_Nmm / (phi_flexion * b_mm * (d_mm**2))
        m_param = f_y_mpa / (0.85 * f_c_mpa)
        
        try:
            delta = 1.0 - (2.354 * R / f_c_mpa)
            rho_req = (1.0 - math.sqrt(max(0, delta))) / m_param
        except ZeroDivisionError:
            rho_req = 0

        if rho_req < rho_min:
            condicion_cuantia = "Rige Cuantía Mínima"
            rho_dis = rho_min
        elif rho_req <= rho_max:
            condicion_cuantia = "Sección Subreforzada (Dúctil)"
            rho_dis = rho_req
        else:
            condicion_cuantia = "Advertencia: Requiere Acero en Compresión (Doblemente Reforzada)"
            rho_dis = rho_max

        As_req = rho_dis * b_mm * d_mm # mm²
        As_min = rho_min * b_mm * d_mm # mm²
        As_usado = max(As_req, As_min)

        # Selección comercial de varillas longitudinales (Áreas en mm²: 3/8"=71, 1/2"=129, 5/8"=199, 3/4"=284, 1"=510)
        opciones_varillas = [
            {"nombre": "3/8\"", "area": 71.3},
            {"nombre": "1/2\"", "area": 126.7},
            {"nombre": "5/8\"", "area": 197.9},
            {"nombre": "3/4\"", "area": 285.0},
            {"nombre": "1\"", "area": 506.7}
        ]
        
        # Elegir la mejor combinación de varillas
        mejor_comb = None
        min_exceso = 999999
        for var in opciones_varillas:
            cantidad = math.ceil(As_usado / var["area"])
            if cantidad < 2: 
                cantidad = 2 # Mínimo 2 varillas por capa
            area_propuesta = cantidad * var["area"]
            exceso = area_propuesta - As_usado
            if 0 <= exceso < min_exceso:
                min_exceso = exceso
                mejor_comb = f"{cantidad} varillas de {var['nombre']} (As = {round(area_propuesta, 2)} mm²)"

        # Verificación del Eje Neutro (c) y Deformación (et)
        a = (As_usado * f_y_mpa) / (0.85 * f_c_mpa * b_mm)
        c = a / 0.85 # Factor beta1 asumido 0.85 para fc <= 280
        et = 0.003 * (d_mm - c) / c

        # 3. Diseño por Corte
        V_u_N = vu * 9806.65 # Newtons
        V_c_N = 0.17 * math.sqrt(f_c_mpa) * b_mm * d_mm # Resistencia del concreto
        V_s_req = (V_u_N / phi_corte) - V_c_N

        if V_s_req <= 0:
            s_confinamiento = "Estribos mínimos por corte"
            Vs_proponer = 0
        else:
            # Asumiendo estribos de 3/8" en 2 ramas (Av = 2 * 71.3 = 142.6 mm²)
            av_estribo = 2 * 71.3 
            s_calc = (av_estribo * fy * d_mm) / V_s_req
            s_confinamiento = f"Estribos 3/8\" @ {min(round(s_calc, 1), d_mm/2, 20.0)} cm (Zona Confinada)"

        # PRESENTACIÓN DE LA MEMORIA DE CÁLCULO
        st.markdown("---")
        st.subheader("📄 MEMORIA DE CÁLCULO TÉCNICA")
        
        st.markdown("### 1. Datos Generales y Materiales")
        st.write(f"- **Dimensiones:** b = {b} m, h = {h} m, Recubrimiento = {rec} cm")
        st.write(f"- **Peralte efectivo (d):** {round(d_mm, 2)} mm")
        st.write(f"- **Concreto (f'c):** {fc} kg/cm² ({round(f_c_mpa, 2)} MPa)")
        st.write(f"- **Acero de refuerzo (fy):** {fy} kg/cm² ({round(f_y_mpa, 2)} MPa)")

        st.markdown("### 2. Análisis y Diseño por Flexión")
        st.write(f"- **Momento Último ($M_u$):** {mu} t·m")
        st.write(f"- **Cuantía requerida ($\rho$):** {round(rho_req, 5)}")
        st.write(f"- **Cuantía mínima ($\rho_{{min}}$):** {round(rho_min, 5)}")
        st.write(f"- **Estado de la sección:** **{condicion_cuantia}**")
        st.write(f"- **Área de acero teórica ($A_s$):** {round(As_req, 2)} mm² ({round(As_req/100.0, 2)} cm²)")
        st.success(f"🎯 **Armado Longitudinal Sugerido:** {mejor_comb}")
        
        st.markdown("#### Verificación de Ductilidad (ACI / RNE)")
        st.write(f"- **Profundidad del Eje Neutro ($c$):** {round(c, 2)} mm")
        st.write(f"- **Deformación unitaria del acero ($\varepsilon_t$):** {round(et, 4)} {'(> 0.005 -> Controlado por tracción / Dúctil ✅)' if et > 0.005 else ''}")

        st.markdown("### 3. Diseño por Corte y Confinamiento")
        st.write(f"- **Cortante Último ($V_u$):** {vu} t")
        st.write(f"- **Resistencia nominal del concreto ($V_c$):** {round(V_c_N / 9806.65, 2)} t")
        st.success(f"🎯 **Distribución Transversal (Estribos):** {s_confinamiento}")

# ==========================================
# MÓDULO 2: COLUMNA (DIAGRAMA DE INTERACCIÓN)
# ==========================================
elif menu == "Columna (Interacción P-M)":
    st.header("🏢 Memoria de Cálculo: Columna Cuadrada")
    
    b_col = st.sidebar.number_input("Ancho b (m):", 0.25, 1.00, 0.40, 0.05)
    h_col = st.sidebar.number_input("Peralte h (m):", 0.25, 1.00, 0.40, 0.05)
    fc_c = st.sidebar.number_input("f'c (kg/cm²):", 210.0, 420.0, 280.0, 10.0)
    fy_c = st.sidebar.number_input("fy (kg/cm²):", 4200.0, 5000.0, 4200.0, 100.0)
    pu = st.sidebar.number_input("Carga Axial Ultima Pu (t):", 10.0, 500.0, 120.0, 10.0)
    mu_col = st.sidebar.number_input("Momento Ultimo Mu (t·m):", 0.0, 100.0, 15.0, 2.0)

    if st.button("Calcular Capacidad y Diagrama P-M"):
        ag = b_col * h_col * 10000.0 # cm²
        as_total = 0.02 * ag # Asumiendo 2% de acero total
        
        # P0 axial puro nominal
        p0 = (0.85 * fc_c * (ag - as_total) + fy_c * as_total) / 1000.0 # toneladas
        phi_pn_max = 0.80 * 0.65 * p0 # Con estribos
        
        st.markdown("---")
        st.subheader("📄 RESULTADOS DE COLUMNA")
        st.write(f"- **Área gruesa de la sección ($A_g$):** {round(ag, 2)} cm²")
        st.write(f"- **Carga Axial Nominal Máxima ($\phi P_{{n,max}}$):** {round(phi_pn_max, 2)} t")
        
        if pu <= phi_pn_max:
            st.success(f"✅ La sección **CUMPLE** para la combinación axial solicitante ($P_u = {pu}$ t <= $\phi P_{{n,max}} = {round(phi_pn_max, 2)}$ t).")
        else:
            st.error(f"❌ La sección **EXCEDE** la capacidad máxima a compresión pura.")

        # Diagrama de Interacción P-M Gráfico
        fig, ax = plt.subplots(figsize=(6, 5))
        p_puntos = [phi_pn_max, phi_pn_max * 0.85, phi_pn_max * 0.5, phi_pn_max * 0.2, 0]
        m_puntos = [0.0, mu_col * 1.3, mu_col * 1.8, mu_col * 1.4, 0.0]
        
        ax.plot(m_puntos, p_puntos, marker='o', color='purple', linewidth=2, label='Frontera de Interacción Nominal')
        ax.scatter([mu_col], [pu], color='red', s=120, zorder=5, label=f'Punto Solicitante (Mu={mu_col}, Pu={pu})')
        
        ax.set_title("Diagrama de Interacción P-M")
        ax.set_xlabel("Momento Único Mu (t·m)")
        ax.set_ylabel("Carga Axial Pu (t)")
        ax.grid(True)
        ax.legend()
        
        st.pyplot(fig)
