import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Diseño de Vigas y Columnas MKS", layout="centered")

st.title("🏗️ Memoria de Cálculo Estructural (Norma ACI / RNE)")
st.write("Herramienta interactiva para diseño por flexión y corte en elementos de concreto armado.")

# Menú lateral para elegir el elemento
menu = st.sidebar.selectbox("Seleccione el elemento a diseñar:", ["Viga Rectangular", "Columna Cuadrada"])

# ==========================================
# MÓDULO DE VIGA RECTANGULAR
# ==========================================
if menu == "Viga Rectangular":
    st.header("📐 Diseño por Flexión y Corte - Viga Rectangular")
    
    col1, col2 = st.columns(2)
    with col1:
        b = st.number_input("Ancho de la viga (b en m):", min_value=0.10, max_value=2.00, value=0.30, step=0.05)
        h = st.number_input("Peralte total (h en m):", min_value=0.10, max_value=3.00, value=0.50, step=0.05)
        rec = st.number_input("Recubrimiento libre (cm):", min_value=1.0, max_value=10.0, value=4.0, step=0.5)
    with col2:
        fc = st.number_input("Resistencia del concreto (f'c en kg/cm²):", min_value=140.0, max_value=500.0, value=210.0, step=10.0)
        fy = st.number_input("Fluencia del acero (fy en kg/cm²):", min_value=2800.0, max_value=5000.0, value=4200.0, step=100.0)
        mu = st.number_input("Momento último (Mu en t·m):", min_value=0.1, max_value=200.0, value=12.5, step=0.5)
        vu = st.number_input("Cortante último (Vu en t):", min_value=0.0, max_value=100.0, value=8.0, step=0.5)

    if st.button("Calcular Memoria de Cálculo de Viga"):
        # Conversiones y cálculos internos
        f_c_mpa = fc / 10.197
        f_y_mpa = fy / 10.197
        d = h - (rec / 100.0)
        
        phi_flexion = 0.9
        phi_corte = 0.75
        
        M_u_Nm = mu * 9806.65
        b_m = b
        
        # Cuantías
        rho_min = max(0.25 * math.sqrt(f_c_mpa) / f_y_mpa, 1.4 / f_y_mpa)
        rho_max = 0.85 * f_c_mpa / f_y_mpa * (600 / (600 + f_y_mpa))
        
        R = M_u_Nm / (phi_flexion * b_m * (d**2))
        m_param = f_y_mpa / (0.85 * f_c_mpa)
        
        try:
            delta = 1.0 - (2.354 * R / f_c_mpa)
            rho_req = (1.0 - math.sqrt(max(0, delta))) / m_param
        except ZeroDivisionError:
            rho_req = 0

        if rho_req < rho_min:
            tipo_ref = "Simple reforzada (Rige Cuantía Mínima)"
            rho_final = rho_min
        elif rho_req <= rho_max:
            tipo_ref = "Simple reforzada"
            rho_final = rho_req
        else:
            tipo_ref = "Doblemente reforzada (Excede cuantía máxima)"
            rho_final = rho_max

        as_req = rho_final * b_m * d * 10000.0 # cm²
        as_min = rho_min * b_m * d * 10000.0 # cm²

        # Corte
        V_u_N = vu * 9806.65
        V_c_N = 0.17 * math.sqrt(f_c_mpa) * (b_m * 1000.0) * (d * 1000.0)
        V_s_req_N = (V_u_N / phi_corte) - V_c_N

        st.subheader("📋 Resultados del Análisis y Diseño")
        
        st.markdown("### 1. Parámetros Geométricos y Materiales")
        st.write(f"- **Peralte efectivo (d):** {round(d, 3)} m")
        st.write(f"- **Concreto (f'c):** {fc} kg/cm² ({round(f_c_mpa, 2)} MPa)")
        st.write(f"- **Acero (fy):** {fy} kg/cm² ({round(f_y_mpa, 2)} MPa)")

        st.markdown("### 2. Diseño por Flexión")
        st.write(f"- **Momento Último (Mu):** {mu} t·m")
        st.write(f"- **Tipo de Sección:** {tipo_ref}")
        st.write(f"- **Cuantía calculada / Usada:** {round(rho_final, 5)}")
        st.success(f"**Área de Acero Longitudinal Requerida (As):** {round(as_req, 2)} cm²")
        st.info(f"Área de Acero Mínima: {round(as_min, 2)} cm²")

        st.markdown("### 3. Diseño por Corte y Estribos")
        st.write(f"- **Cortante Último (Vu):** {vu} t")
        st.write(f"- **Resistencia del Concreto (Vc):** {round(V_c_N / 9806.65, 2)} t")
        if V_s_req_N <= 0:
            st.success("- **Estado:** El concreto absorbe el corte; se colocan estribos mínimos por norma.")
        else:
            st.warning(f"- **Estado:** Requiere refuerzo transversal por corte (Vs = {round(V_s_req_N / 9806.65, 2)} t).")

# ==========================================
# MÓDULO DE COLUMNA CUADRADA
# ==========================================
elif menu == "Columna Cuadrada":
    st.header("🏢 Verificación y Diseño - Columna Cuadrada")
    
    col1, col2 = st.columns(2)
    with col1:
        b_col = st.number_input("Dimensión b (m):", min_value=0.20, max_value=1.50, value=0.40, step=0.05)
        h_col = st.number_input("Dimensión h (m):", min_value=0.20, max_value=1.50, value=0.40, step=0.05)
        rec_col = st.number_input("Recubrimiento (cm):", min_value=2.0, max_value=10.0, value=4.0, step=0.5)
    with col2:
        fc_col = st.number_input("f'c (kg/cm²):", min_value=140.0, max_value=500.0, value=280.0, step=10.0)
        fy_col = st.number_input("fy (kg/cm²):", min_value=2800.0, max_value=5000.0, value=4200.0, step=100.0)
        pu_col = st.number_input("Carga Axial Última (Pu en t):", min_value=0.0, max_value=500.0, value=120.0, step=5.0)

    if st.button("Generar Diagrama y Verificación"):
        f_c_mpa = fc_col / 10.197
        f_y_mpa = fy_col / 10.197
        ag = b_col * h_col * 10000.0 # cm²
        
        # Estimación simplificada de capacidad axial pura a compresión (P0)
        # Asumiendo 2% de acero longitudinal aproximado
        as_est = 0.02 * ag
        p0_kg = 0.85 * fc_col * (ag - as_est) + fy_col * as_est
        pmax_t = (0.80 * p0_kg * 0.65) / 1000.0 # Con estribos y factor phi=0.65

        st.subheader("📋 Resultados de Columna")
        st.write(f"- **Área Gruesa (Ag):** {round(ag, 2)} cm²")
        st.write(f"- **Carga Axial Máxima Admisible (phi*Pns):** {round(pmax_t, 2)} t")

        if pu_col <= pmax_t:
            st.success(f"✅ La columna **CUMPLE** bajo la carga axial solicitante (Pu = {pu_col} t <= Pmax = {round(pmax_t, 2)} t).")
        else:
            st.error(f"❌ La columna **FALLA** por exceso de carga axial (Pu = {pu_col} t > Pmax = {round(pmax_t, 2)} t). Incremente la sección.")

        # Generar Gráfico de Interacción Simplificado
        st.markdown("### 📊 Diagrama de Interacción P-M Esquemático")
        fig, ax = plt.subplots(figsize=(6, 5))
        
        # Puntos aproximados de control del diagrama de interacción
        p_axiales = [pmax_t, pmax_t * 0.8, pmax_t * 0.4, 0, -pmax_t * 0.3]
        m_momentos = [0, 15.0, 25.0, 18.0, 0]
        
        ax.plot(m_momentos, p_axiales, marker='o', color='b', label='Capacidad Nominal Interacción')
        ax.scatter([5.0], [pu_col], color='r', s=100, zorder=5, label=f'Punto Solicitante (Pu={pu_col}t)')
        
        ax.set-title ? # Corregido abajo en texto plano
        ax.set_title("Diagrama de Interacción P - M")
        ax.set_xlabel("Momento Único / Nominal (t·m)")
        ax.set_ylabel("Carga Axial Pu (t)")
        ax.grid(True)
        ax.legend()
        
        st.pyplot(fig)
