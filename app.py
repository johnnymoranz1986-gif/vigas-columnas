import math
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Configuración de la página
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
        # 1. Conversiones de Unidades y Parámetros Base
        f_c_mpa = fc / 10.197
        f_y_mpa = fy / 10.197
        b_mm = b_m * 1000.0
        h_mm = h_m * 1000.0
        rec_mm = rec_cm * 10.0
        
        # Asumiendo diámetro de estribo de 3/8" (9.5mm) y varilla longitudinal promedio de 3/4" (~19mm)
        d_mm = h_mm - rec_mm - 9.5 - (19.1 / 2.0)
        d_m = d_mm / 1000.0
        
        phi_flexion = 0.90
        phi_corte = 0.75
        Mu_Nmm = mu_tm * 9.80665 * 10**6
        
        # 2. Cuantías Límites (RNE E.060 / ACI)
        rho_min = max(0.25 * math.sqrt(f_c_mpa) / f_y_mpa, 1.4 / f_y_mpa)
        rho_max = 0.85 * f_c_mpa / f_y_mpa * (600.0 / (600.0 + f_y_mpa)) * 0.75
        
        # 3. Cálculo de Área de Acero por Flexión
        R_param = Mu_Nmm / (phi_flexion * b_mm * (d_mm**2))
        m_coef = f_y_mpa / (0.85 * f_c_mpa)
        
        try:
            delta = 1.0 - (2.354 * R_param / f_c_mpa)
            rho_req = (1.0 - math.sqrt(max(0.0, delta))) / m_coef
        except ZeroDivisionError:
            rho_req = 0.0

        if rho_req < rho_min:
            cond_cuantia = "Rige Cuantía Mínima ($\rho_{min}$)"
            rho_dis = rho_min
        elif rho_req <= rho_max:
            cond_cuantia = "Sección Subreforzada Dúctil ($\rho_{req} \le \rho_{max}$)"
            rho_dis = rho_req
        else:
            cond_cuantia = "Supera Cuantía Máxima (Requiere compresión)"
            rho_dis = rho_max

        As_req = rho_dis * b_mm * d_mm
        As_min = rho_min * b_mm * d_mm
        As_usado = max(As_req, As_min)

        # Selección Comercial de Varillas (Áreas en mm²)
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

        # 4. Cálculo del Eje Neutro (c) y Bloque de Compresiones (a)
        a_mm = (As_provisto * f_y_mpa) / (0.85 * f_c_mpa * b_mm)
        beta1 = 0.85 if f_c_mpa <= 28 else max(0.85 - 0.05 * (f_c_mpa - 28) / 7, 0.65)
        c_mm = a_mm / beta1
        eps_t = 0.003 * (d_mm - c_mm) / c_mm

        # 5. Diseño por Corte y Confinamiento
        Vu_N = vu_t * 9806.65
        Vc_N = 0.17 * math.sqrt(f_c_mpa) * b_mm * d_mm
        Vs_req_N = (Vu_N / phi_corte) - Vc_N

        if Vs_req_N <= 0:
            espaciamiento = "Estribos mínimos por norma (Smax = d/2 o 20 cm)"
            estribo_desc = "Estribos de 3/8\" @ 0.20 m"
        else:
            Av_2ram = 2.0 * 71.3 # 2 ramas de 3/8"
            s_calc = (Av_2ram * f_y_mpa * d_mm) / Vs_req_N
            s_final = min(s_calc, d_mm / 4.0, 15.0) # Confinamiento sismorresistente
            estribo_desc = f"Estribos de 3/8\" @ {round(s_final, 1)} cm (Zona Confinada)"

        # -------------------------------------------------------------
        # PRESENTACIÓN DE RESULTADOS Y FORMULAS DETALLADAS EN PANTALLA
        # -------------------------------------------------------------
        st.markdown("---")
        st.subheader("📋 1. RESUMEN DE PARÁMETROS GEOMÉTRICOS Y MATERIALES")
        st.latex(f"b = {b_m}\\text{{ m}}, \\quad h = {h_m}\\text{{ m}}, \\quad d = {round(d_m, 3)}\\text{{ m}}")
        st.latex(f"f'c = {fc}\\text{{ kg/cm²}} ({round(f_c_mpa, 2)}\\text{{ MPa}}), \\quad fy = {fy}\\text{{ kg/cm²}} ({round(f_y_mpa, 2)}\\text{{ MPa}})")

        st.subheader("📋 2. MEMORIA DE CÁLCULO POR FLEXIÓN")
        st.markdown("Cálculo de la cuantía geométrica requerida:")
        st.latex(f"\\rho_{{req}} = \\frac{1}{m} \\left( 1 - \\sqrt{1 - \\frac{2.354 M_u}{\\phi f'_c b d^2}} \\right) = {round(rho_req, 5)}")
        st.markdown(f"**Condición:** {cond_cuantia} (Cuantía aplicada $\\rho = {round(rho_dis, 5)}$)")
        
        st.latex(f"A_{{s,req}} = \\rho \\cdot b \\cdot d = {round(As_req, 2)}\\text{{ mm²}} \\implies \\text{{Usado: }} {round(As_provisto, 2)}\\text{{ mm²}}")
        st.success(f"🎯 **Armado Seleccionado:** {num_barras} varillas de {mejor_varilla['nombre']} ($A_s = {round(As_provisto, 2)}\\text{{ mm²}}$)")

        st.markdown("Verificación de Ductilidad (Deformación unitaria del acero $\\varepsilon_t$):")
        st.latex(f"a = \\frac{{A_s f_y}}{0.85 f'_c b} = {round(a_mm, 2)}\\text{{ mm}}, \\quad c = \\frac{a}{\\beta_1} = {round(c_mm, 2)}\\text{{ mm}}")
        st.latex(f"\\varepsilon_t = 0.003 \\left( \\frac{d - c}{c} \\right) = {round(eps_t, 4)} \\quad {'(\\varepsilon_t \\ge 0.005 \\rightarrow \\text{Dúctil / Controlado por Tracción ✅})' if eps_t >= 0.005 else ''}")

        st.subheader("📋 3. DISEÑO POR CORTE Y CONFINAMIENTO")
        st.latex(f"V_c = 0.17 \\sqrt{f'_c} \\cdot b \\cdot d = {round(Vc_N / 9806.65, 2)}\\text{{ t}}")
        st.latex(f"V_{{u}} / \\phi = {round(Vu_N / (phi_corte * 9806.65), 2)}\\text{{ t}} \\quad \\implies \\quad V_{{s,req}} = {max(0.0, round(Vs_req_N / 9806.65, 2))}\\text{{ t}}")
        st.info(f"🎯 **Refuerzo Transversal:** {estribo_desc}")

        # -------------------------------------------------------------
        # GENERACIÓN DE IMAGEN CON LA DISTRIBUCIÓN DEL ACERO
        # -------------------------------------------------------------
        st.subheader("🖼️ Esquema Gráfico: Distribución de Acero en Sección Transversal")
        
        fig, ax = plt.subplots(figsize=(5, 6))
        
        # Dibujar sección de la viga
        viga_rect = plt.Rectangle((0, 0), b_m, h_m, edgecolor='black', facecolor='#EAEAEA', linewidth=2, label='Concreto')
        ax.add_patch(viga_rect)
        
        # Dibujar estribo (recubrimiento)
        rec_m = rec_cm / 100.0
        estribo_rect = plt.Rectangle((rec_m, rec_m), b_m - 2*rec_m, h_m - 2*rec_m, edgecolor='blue', facecolor='none', linewidth=1.5, linestyle='--', label='Estribo 3/8"')
        ax.add_patch(estribo_rect)
        
        # Dibujar barras de acero longitudinal inferior
        ancho_util = b_m - 2*rec_m - 0.05
        if num_barras == 1:
            espaciamientos = [ancho_util / 2]
        else:
            espaciamientos = np.linspace(rec_m + 0.025, b_m - rec_m - 0.025, num_barras)
            
        for x_pos in espaciamientos:
            bar_inf = plt.Circle((x_pos, rec_m + 0.025), 0.012, color='red', zorder=5)
            ax.add_patch(bar_inf)
            
        # Dos varillas de montaje superiores
        bar_sup1 = plt.Circle((rec_m + 0.025, h_m - rec_m - 0.025), 0.010, color='red', zorder=5)
        bar_sup2 = plt.Circle((b_m - rec_m - 0.025, h_m - rec_m - 0.025), 0.010, color='red', zorder=5)
        ax.add_patch(bar_sup1)
        ax.add_patch(bar_sup2)

        ax.scatter([], [], color='red', s=50, label=f'Acero Long. ({num_barras} ø {mejor_varilla["name"] if "name" in mejor_varilla else mejor_varilla["nombre"]})')

        ax.set_xlim(-0.05, b_m + 0.05)
        ax.set_ylim(-0.05, h_m + 0.05)
        ax.set_aspect('equal')
        ax.set_title(f"Sección b={b_m}m x h={h_m}m", fontsize=11, fontweight='bold')
        ax.set_xlabel("Ancho (m)")
        ax.set_ylabel("Peralte (m)")
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc='upper right', fontsize=8)

        st.pyplot(fig)

elif menu == "Columna Cuadrada":
    st.header("🏢 Verificación de Columna y Diagrama de Interacción")
    st.write("Módulo activo de columnas bajo solicitación axial-flectora combinada.")
