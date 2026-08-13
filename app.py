import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Memoria de Cálculo Estructural Avanzada", layout="centered")

st.title("🏗️ Memoria de Cálculo Detallada: Concreto Armado")
st.write("Normativa: Reglamento Nacional de Edificaciones (RNE E.060) / ACI 318")

menu = st.sidebar.selectbox("Seleccione el elemento:", ["Viga Rectangular (Flexión, Corte y Detallado)", "Columna Cuadrada"])

if menu == "Viga Rectangular (Flexión, Corte y Detallado)":
    st.header("📐 Memoria de Cálculo por Flexión y Corte - Viga")
    
    st.sidebar.subheader("Parámetros de Diseño")
    b_m = st.sidebar.number_input("Ancho b (m):", 0.15, 1.00, 0.30, 0.05)
    h_m = st.sidebar.number_input("Peralte h (m):", 0.20, 1.50, 0.50, 0.05)
    rec_cm = st.sidebar.number_input("Recubrimiento libre (cm):", 2.0, 8.0, 4.0, 0.5)
    
    fc = st.sidebar.number_input("f'c (kg/cm²):", 175.0, 420.0, 210.0, 10.0)
    fy = st.sidebar.number_input("fy (kg/cm²):", 2800.0, 5000.0, 4200.0, 100.0)
    
    mu_tm = st.sidebar.number_input("Momento Último Mu (t·m):", 1.0, 300.0, 14.5, 0.5)
    vu_t = st.sidebar.number_input("Cortante Último Vu (t):", 0.5, 150.0, 8.2, 0.5)

    if st.button("Ejecutar Memoria de Cálculo Detallada"):
        f_c_mpa = fc / 10.197
        f_y_mpa = fy / 10.197
        b_mm = b_m * 1000.0
        h_mm = h_m * 1000.0
        rec_mm = rec_cm * 10.0
        
        d_mm = h_mm - rec_mm - 9.5 - (19.1 / 2.0)
        d_m = d_mm / 1000.0
        
        phi_flexion = 0.90
        phi_corte = 0.75
        Mu_Nmm = mu_tm * 9.80665 * 10**6
        
        rho_min = max(0.25 * math.sqrt(f_c_mpa) / f_y_mpa, 1.4 / f_y_mpa)
        rho_max = 0.85 * f_c_mpa / f_y_mpa * (600.0 / (600.0 + f_y_mpa)) * 0.75
        
        R_param = Mu_Nmm / (phi_flexion * b_mm * (d_mm**2))
        m_coef = f_y_mpa / (0.85 * f_c_mpa)
        
        try:
            delta = 1.0 - (2.354 * R_param / f_c_mpa)
            rho_req = (1.0 - math.sqrt(max(0.0, delta))) / m_coef
        except ZeroDivisionError:
            rho_req = 0.0

        if rho_req < rho_min:
            cond_cuantia = "Rige Cuantía Mínima"
            rho_dis = rho_min
        elif rho_req <= rho_max:
            cond_cuantia = "Sección Subreforzada Dúctil"
            rho_dis = rho_req
        else:
            cond_cuantia = "Supera Cuantía Máxima"
            rho_dis = rho_max

        As_req = rho_dis * b_mm * d_mm
        As_min = rho_min * b_mm * d_mm
        As_usado = max(As_req, As_min)

        catalogo = [
            {"nombre": "3/8\"", "area": 71.3},
            {"nombre": "1/2\"", "area": 126.7},
            {"nombre": "5/8\"", "area": 197.9},
            {"nombre": "3/4\"", "area": 285.0},
            {"nombre": "1\"", "area": 506.7}
        ]
        
        mejor_varilla = None
        num_barras = 2
        min_exceso = 999999
        for var in catalogo:
            cant = math.ceil(As_usado / var["area"])
            if cant < 2: 
                cant = 2
            area_prop = cant * var["area"]
            exceso = area_prop - As_usado
            if 0 <= exceso < min_exceso:
                min_exceso = exceso
                num_barras = cant
                mejor_varilla = var

        As_provisto = num_barras * mejor_varilla["area"]

        a_mm = (As_provisto * f_y_mpa) / (0.85 * f_c_mpa * b_mm)
        beta1 = 0.85 if f_c_mpa <= 28 else max(0.85 - 0.05 * (f_c_mpa - 28) / 7, 0.65)
        c_mm = a_mm / beta1
        eps_t = 0.003 * (d_mm - c_mm) / c_mm

        Vu_N = vu_t * 9806.65
        Vc_N = 0.17 * math.sqrt(f_c_mpa) * b_mm * d_mm
        Vs_req_N = (Vu_N / phi_corte) - Vc_N

        if Vs_req_N <= 0:
            estribo_desc = "Estribos de 3/8\" @ 0.20 m (Mínimos por norma)"
        else:
            Av_2ram = 2.0 * 71.3 
            s_calc = (Av_2ram * f_y_mpa * d_mm) / Vs_req_N
            s_final = min(s_calc, d_mm / 4.0, 15.0)
            estribo_desc = f"Estribos de 3/8\" @ {round(s_final, 1)} cm (Zona Confinada)"

        st.markdown("---")
        st.subheader("📋 1. RESUMEN DE PARÁMETROS GEOMÉTRICOS Y MATERIALES")
        st.write(f"- Ancho (b): {b_m} m | Peralte (h): {h_m} m | Peralte efectivo (d): {round(d_m, 3)} m")
        st.write(f"- Concreto (f'c): {fc} kg/cm² ({round(f_c_mpa, 2)} MPa) | Acero (fy): {fy} kg/cm² ({round(f_y_mpa, 2)} MPa)")

        st.subheader("📋 2. MEMORIA DE CÁLCULO POR FLEXIÓN")
        st.write(f"- Cuantía geométrica requerida (rho_req): {round(rho_req, 5)}")
        st.write(f"- Condición aplicada: {cond_cuantia} (Cuantía usada: {round(rho_dis, 5)})")
        st.write(f"- Área de acero teórica (As): {round(As_req, 2)} mm² ({round(As_req/100.0, 2)} cm²)")
        st.success(f"🎯 **Armado Seleccionado:** {num_barras} varillas de {mejor_varilla['nombre']} (As provisto = {round(As_provisto, 2)} mm²)")

        st.write(f"- Profundidad del bloque de compresión (a): {round(a_mm, 2)} mm")
        st.write(f"- Profundidad del eje neutro (c): {round(c_mm, 2)} mm")
        st.write(f"- Deformación unitaria del acero (eps_t): {round(eps_t, 4)} {'(Dúctil / Controlado por Tracción ✅)' if eps_t >= 0.005 else ''}")

        st.subheader("📋 3. DISEÑO POR CORTE Y CONFINAMIENTO")
        st.write(f"- Resistencia nominal del concreto (Vc): {round(Vc_N / 9806.65, 2)} t")
        st.write(f"- Cortante absorbido por el acero (Vs): {max(0.0, round(Vs_req_N / 9806.65, 2))} t")
        st.info(f"🎯 **Refuerzo Transversal:** {estribo_desc}")

        st.subheader("🖼️ Esquema Gráfico: Distribución de Acero en Sección Transversal")
        
        fig, ax = plt.subplots(figsize=(5, 6))
        viga_rect = plt.Rectangle((0, 0), b_m, h_m, edgecolor='black', facecolor='#EAEAEA', linewidth=2, label='Concreto')
        ax.add_patch(viga_rect)
        
        rec_m = rec_cm / 100.0
        estribo_rect = plt.Rectangle((rec_m, rec_m), b_m - 2*rec_m, h_m - 2*rec_m, edgecolor='blue', facecolor='none', linewidth=1.5, linestyle='--', label='Estribo')
        ax.add_patch(estribo_rect)
        
        ancho_util = b_m - 2*rec_m - 0.05
        if num_barras == 1:
            espaciamientos = [ancho_util / 2]
        else:
            espaciamientos = np.linspace(rec_m + 0.025, b_m - rec_m - 0.025, num_barras)
            
        for x_pos in espaciamientos:
            bar_inf = plt.Circle((x_pos, rec_m + 0.025), 0.012, color='red', zorder=5)
            ax.add_patch(bar_inf)
            
        bar_sup1 = plt.Circle((rec_m + 0.025, h_m - rec_m - 0.025), 0.010, color='red', zorder=5)
        bar_sup2 = plt.Circle((b_m - rec_m - 0.025, h_m - rec_m - 0.025), 0.010, color='red', zorder=5)
        ax.add_patch(bar_sup1)
        ax.add_patch(bar_sup2)

        ax.set_xlim(-0.05, b_m + 0.05)
        ax.set_ylim(-0.05, h_m + 0.05)
        ax.set_aspect('equal')
        ax.set_title(f"Sección b={b_m}m x h={h_m}m", fontsize=11, fontweight='bold')
        ax.set_xlabel("Ancho (m)")
        ax.set_ylabel("Peralte (m)")
        ax.grid(True, linestyle=':', alpha=0.6)

        st.pyplot(fig)

elif menu == "Columna Cuadrada":
    st.header("🏢 Verificación de Columna y Diagrama de Interacción")
    st.write("Módulo activo de columnas bajo solicitación axial-flectora combinada.")
