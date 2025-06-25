import streamlit as st
import pandas as pd
from lxml import etree
from datetime import datetime
import plotly.express as px
from auth import check_login, register_user, get_users
import io
import os
import xmlschema

# --- Definir funciones auxiliares primero ---
def is_valid_date(val):
    try:
        pd.to_datetime(val, format='%Y-%m-%d')
        return True
    except:
        return False

def is_valid_number(val):
    try:
        float(val)
        return True
    except:
        return False

st.set_page_config(page_title="IATI Pipeline", layout="wide")

# --- Autenticación ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''

if not st.session_state['logged_in']:
    st.markdown("""
        <style>
        @media (prefers-color-scheme: dark) {
            .login-card {
                background: linear-gradient(135deg, #232526 0%, #414345 100%) !important;
                color: #fff !important;
                box-shadow: 0 8px 32px 0 rgba(0,0,0,0.45);
                border-radius: 1.5rem;
                padding: 2.5rem 2rem 2rem 2rem;
                max-width: 420px;
                margin: 2.5rem auto;
                border: 1px solid #333;
            }
            .login-title {
                color: #ff4b4b !important;
                text-align: center;
                font-size: 2.2rem;
                font-weight: 800;
                margin-bottom: 1.2rem;
                letter-spacing: 1px;
            }
            .login-subtitle {
                color: #b0b0b0 !important;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }
            .stTextInput>div>div>input {
                background: #2d2d2d !important;
                color: #fff !important;
                border-radius: 0.6rem;
                border: 1px solid #cc0407;
                font-size: 1.1rem;
            }
            .stButton>button {
                background: linear-gradient(90deg, #cc0407 0%, #ff4b4b 100%) !important;
                color: #fff !important;
                border-radius: 0.6rem;
                font-weight: 700;
                padding: 0.6rem 1.7rem;
                font-size: 1.1rem;
                margin-top: 0.7rem;
                box-shadow: 0 2px 8px 0 rgba(204,4,7,0.10);
                border: none;
                transition: background 0.2s;
            }
            .stButton>button:hover {
                background: linear-gradient(90deg, #a80000 0%, #cc0407 100%) !important;
            }
        }
        @media (prefers-color-scheme: light) {
            .login-card {
                background: linear-gradient(135deg, #f5f7fa 0%, #fbe9e7 100%);
                color: #222;
                box-shadow: 0 8px 32px 0 rgba(0,0,0,0.10);
                border-radius: 1.5rem;
                padding: 2.5rem 2rem 2rem 2rem;
                max-width: 420px;
                margin: 2.5rem auto;
                border: 1px solid #e0e0e0;
            }
            .login-title {
                color: #cc0407;
                text-align: center;
                font-size: 2.2rem;
                font-weight: 800;
                margin-bottom: 1.2rem;
                letter-spacing: 1px;
            }
            .login-subtitle {
                color: #555;
                text-align: center;
                margin-bottom: 2rem;
                font-size: 1.1rem;
            }
            .stTextInput>div>div>input {
                background: #f5f6fa;
                color: #222;
                border-radius: 0.6rem;
                border: 1px solid #cc0407;
                font-size: 1.1rem;
            }
            .stButton>button {
                background: linear-gradient(90deg, #cc0407 0%, #ff4b4b 100%);
                color: #fff;
                border-radius: 0.6rem;
                font-weight: 700;
                padding: 0.6rem 1.7rem;
                font-size: 1.1rem;
                margin-top: 0.7rem;
                box-shadow: 0 2px 8px 0 rgba(204,4,7,0.10);
                border: none;
                transition: background 0.2s;
            }
            .stButton>button:hover {
                background: linear-gradient(90deg, #a80000 0%, #cc0407 100%);
            }
        }
        /* Oculta solo la barra ovalada negra de las tabs de Streamlit */
        [data-testid="stTabs"] [data-testid="stTabsHighlight"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-card" style="padding-top: 1.2rem;">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">FONPLATA - IATI Pipeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Inicia sesión o regístrate para continuar</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])
        with tab1:
            username = st.text_input("Usuario", key="login_user")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            if st.button("Ingresar", key="login_btn"):
                if check_login(username, password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success("¡Bienvenido, {}!".format(username))
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos")
        with tab2:
            new_user = st.text_input("Nuevo usuario", key="reg_user")
            new_pass = st.text_input("Nueva contraseña", type="password", key="reg_pass")
            if st.button("Registrar", key="reg_btn"):
                if register_user(new_user, new_pass):
                    st.success("Usuario registrado. Ahora puedes iniciar sesión.")
                else:
                    st.error("El usuario ya existe.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- App principal ---
st.sidebar.title(f"Bienvenido, {st.session_state['username']}")
page = st.sidebar.selectbox("Navegación", ["Conversión Estándar de IATI", "Ver tablas", "Curva de desembolsos", "Validar XML IATI"])

if 'df_activities' not in st.session_state:
    st.session_state['df_activities'] = None
if 'df_transactions' not in st.session_state:
    st.session_state['df_transactions'] = None

if page == "Conversión Estándar de IATI":
    st.header("Subir archivo Excel y convertir a XML IATI")
    uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])
    if uploaded_file:
        xls = pd.ExcelFile(uploaded_file)
        if 'Actividades' in xls.sheet_names and 'Transacciones' in xls.sheet_names:
            df_activities = pd.read_excel(xls, sheet_name='Actividades')
            df_transactions = pd.read_excel(xls, sheet_name='Transacciones')
            st.session_state['df_activities'] = df_activities
            st.session_state['df_transactions'] = df_transactions

            # --- VALIDACIÓN ESTRICTA DEL EXCEL ---
            errors = []
            # Participating-org role obligatorio y válido
            valid_roles = {"1", "2", "3", "4"}  # funding, accountable, extending, implementing
            valid_types = {"10", "21", "22", "23", "24", "40", "60", "70", "80", "90"}  # Ejemplo, puedes ampliar
            # Fechas válidas
            date_type_map = {
                "activity-date@type=start-planned": "1",
                "activity-date@type=start-actual": "2",
                "activity-date@type=end-planned": "3",
                "activity-date@type=end-actual": "4"
            }
            # Sector obligatorio
            sector_at_activity = df_activities["sector/@code"].notnull().all() if "sector/@code" in df_activities.columns else False
            sector_at_transaction = "sector/@code" in df_transactions.columns and df_transactions["sector/@code"].notnull().all()
            # Validación por actividad
            for idx, act in df_activities.iterrows():
                # Participating-org role
                role = str(act.get("participating-org/@role", "")).strip()
                if not role or role not in valid_roles:
                    errors.append(f"Fila {idx+2} de 'Actividades': 'participating-org/@role' es obligatorio y debe ser uno de {valid_roles}.")
                # Participating-org type (opcional, pero si está debe ser válido)
                type_ = str(act.get("participating-org/@type", "")).strip()
                if type_ and type_ not in valid_types:
                    errors.append(f"Fila {idx+2} de 'Actividades': 'participating-org/@type' debe ser uno de {valid_types} si se especifica.")
                # Fechas: al menos una de inicio
                has_start = False
                for k in ["activity-date@type=start-planned", "activity-date@type=start-actual"]:
                    val = str(act.get(k, "")).strip()
                    if val:
                        has_start = True
                        # Validar formato fecha
                        if not is_valid_date(val):
                            errors.append(f"Fila {idx+2} de 'Actividades': '{k}' debe tener formato AAAA-MM-DD.")
                if not has_start:
                    errors.append(f"Fila {idx+2} de 'Actividades': Debe tener al menos una fecha de inicio (planned o actual).")
                # Sector a nivel actividad
                if not sector_at_activity and not sector_at_transaction:
                    errors.append(f"Fila {idx+2} de 'Actividades': Debe haber sector a nivel actividad o en todas las transacciones.")
            # Validación por transacción
            if sector_at_transaction:
                for idx, tx in df_transactions.iterrows():
                    if not str(tx.get("sector/@code", "")).strip():
                        errors.append(f"Fila {idx+2} de 'Transacciones': 'sector/@code' es obligatorio si se usa sector a nivel transacción.")
            # Mostrar errores si existen
            if errors:
                st.error("Se encontraron los siguientes errores en tu archivo Excel:")
                for err in errors:
                    st.write(f"- {err}")
                st.stop()
            st.success("Archivo cargado y validado correctamente.")
            # --- Generar XML ---
            def safe(val):
                return "" if pd.isnull(val) else str(val)
            root = etree.Element(
                "iati-activities",
                version="2.03"
            )
            XML_NS = "http://www.w3.org/XML/1998/namespace"
            for _, act in df_activities.iterrows():
                a = etree.SubElement(root, "iati-activity")
                a.set(f"{{{XML_NS}}}lang", "es")
                etree.SubElement(a, "iati-identifier").text = safe(act["iati-identifier"])
                reporg = etree.SubElement(a, "reporting-org",
                    ref=safe(act["reporting-org/@ref"]),
                    type=safe(act["reporting-org/@type"])
                )
                etree.SubElement(reporg, "narrative").text = safe(act["reporting-org/narrative"])
                title = etree.SubElement(a, "title")
                etree.SubElement(title, "narrative").text = safe(act["title/narrative"])
                descr = etree.SubElement(a, "description", type=safe(act.get("description/@type", "1")))
                etree.SubElement(descr, "narrative").text = safe(act["description/narrative"])
                # participating-org (obligatorio, role obligatorio, type opcional)
                role = safe(act.get("participating-org/@role"))
                part_org_attribs = {"role": role}
                ref = safe(act.get("participating-org/@ref"))
                if ref:
                    part_org_attribs["ref"] = ref
                type_ = safe(act.get("participating-org/@type"))
                if type_:
                    part_org_attribs["type"] = type_
                part_org = etree.SubElement(a, "participating-org", **part_org_attribs)
                etree.SubElement(part_org, "narrative").text = safe(act.get("participating-org/narrative"))
                # activity-status
                etree.SubElement(a, "activity-status", code=safe(act["activity-status/@code"]))
                # activity-date (usar códigos numéricos)
                for k, v in date_type_map.items():
                    fecha = safe(act.get(k))
                    if fecha:
                        etree.SubElement(a, "activity-date", attrib={
                            "type": v,
                            "iso-date": fecha[:10]
                        })
                # recipient-country
                if safe(act.get("recipient-country/@code")):
                    etree.SubElement(
                        a, "recipient-country",
                        code=safe(act["recipient-country/@code"])
                    )
                # sector
                if safe(act.get("sector/@code")):
                    sector_attribs = {
                        "code": safe(act["sector/@code"])
                    }
                    vocab = safe(act.get("sector/@vocabulary", "1"))
                    if vocab:
                        sector_attribs["vocabulary"] = vocab
                    etree.SubElement(
                        a, "sector",
                        **sector_attribs
                    )
                # default-finance-type
                if safe(act.get("default-finance-type/@code")):
                    etree.SubElement(a, "default-finance-type", code=safe(act["default-finance-type/@code"]))
                # default-aid-type
                if safe(act.get("default-aid-type/@code")):
                    etree.SubElement(a, "default-aid-type", code=safe(act["default-aid-type/@code"]))
                # budget
                if safe(act.get("budget/period-start")) and safe(act.get("budget/period-end")) and safe(act.get("budget/value")):
                    budget = etree.SubElement(a, "budget")
                    fecha = safe(act["budget/period-start"])
                    if is_valid_date(fecha):
                        etree.SubElement(budget, "period-start", attrib={"iso-date": fecha})
                    fecha = safe(act["budget/period-end"])
                    if is_valid_date(fecha):
                        etree.SubElement(budget, "period-end", attrib={"iso-date": fecha})
                    val = etree.SubElement(budget, "value", currency=safe(act["budget/value/@currency"]))
                    valor = safe(act["budget/value"])
                    if is_valid_number(valor):
                        val.text = valor
                # transacciones (al final)
                activity_id = safe(act["iati-identifier"])
                df_tx = df_transactions[df_transactions["iati-identifier"] == activity_id]
                for _, tx in df_tx.iterrows():
                    t = etree.SubElement(a, "transaction")
                    etree.SubElement(t, "transaction-type", code=safe(tx["transaction-type/@code"]))
                    etree.SubElement(t, "transaction-date", attrib={"iso-date": safe(tx["transaction-date/@iso-date"])[:10]})
                    valor = safe(tx["value"])
                    if is_valid_number(valor):
                        value_attribs = {"currency": safe(tx["value/@currency"])}
                        if safe(tx.get("value/@value-date")):
                            value_attribs["value-date"] = safe(tx["value/@value-date"])
                        val = etree.SubElement(t, "value", **value_attribs)
                        val.text = valor
                    if safe(tx.get("description/narrative")):
                        descr = etree.SubElement(t, "description")
                        etree.SubElement(descr, "narrative").text = safe(tx["description/narrative"])
                    if safe(tx.get("provider-org/@ref")):
                        po = etree.SubElement(t, "provider-org", ref=safe(tx["provider-org/@ref"]))
                        if safe(tx.get("provider-org/narrative")):
                            etree.SubElement(po, "narrative").text = safe(tx["provider-org/narrative"])
                    if safe(tx.get("receiver-org/@ref")):
                        ro = etree.SubElement(t, "receiver-org", ref=safe(tx["receiver-org/@ref"]))
                        if safe(tx.get("receiver-org/narrative")):
                            etree.SubElement(ro, "narrative").text = safe(tx["receiver-org/narrative"])
                    # sector a nivel transacción (si aplica)
                    if safe(tx.get("sector/@code")):
                        sector_attribs = {"code": safe(tx["sector/@code"])}
                        vocab = safe(tx.get("sector/@vocabulary", "1"))
                        if vocab:
                            sector_attribs["vocabulary"] = vocab
                        etree.SubElement(t, "sector", **sector_attribs)
            xml_bytes = etree.tostring(root, encoding="utf-8", pretty_print=True, xml_declaration=True)
            st.download_button("Descargar XML IATI", data=xml_bytes, file_name="output_iati_activities.xml", mime="application/xml")
        else:
            st.error("El archivo debe tener hojas llamadas 'Actividades' y 'Transacciones'.")
    else:
        st.info("Por favor, sube un archivo Excel.")

elif page == "Ver tablas":
    st.header("Tablas del archivo Excel cargado")
    if st.session_state['df_activities'] is not None and st.session_state['df_transactions'] is not None:
        st.subheader("Actividades")
        df_acts = st.session_state['df_activities'].copy()
        # Quitar decimales a columnas numéricas
        for col in df_acts.select_dtypes(include=['float', 'int']).columns:
            df_acts[col] = df_acts[col].astype(float).round(0).astype(int)
        st.data_editor(df_acts, use_container_width=True, hide_index=True, num_rows="dynamic", key="acts_editor")
        st.subheader("Transacciones")
        df_tx = st.session_state['df_transactions'].copy()
        for col in df_tx.select_dtypes(include=['float', 'int']).columns:
            df_tx[col] = df_tx[col].astype(float).round(0).astype(int)
        st.data_editor(df_tx, use_container_width=True, hide_index=True, num_rows="dynamic", key="tx_editor")
    else:
        st.info("Primero sube un archivo Excel en la primera página.")

elif page == "Curva de desembolsos":
    st.header("Curva de desembolsos por proyecto")
    if st.session_state['df_transactions'] is not None:
        df = st.session_state['df_transactions']
        ids = df['iati-identifier'].unique()
        selected_id = st.selectbox("Selecciona el ID del proyecto", ids)
        df_sel = df[df['iati-identifier'] == selected_id]
        # Value box: porcentaje de desembolso respecto a outgoing commitment/aprobacion (tipo 2) para el proyecto seleccionado
        df_tipo3 = df_sel[df_sel['transaction-type/@code'].astype(str).str.strip() == '3']
        outgoing_commitment = df_sel[df_sel['transaction-type/@code'].astype(str).str.strip() == '2']['value']
        if not outgoing_commitment.empty:
            total_commitment = outgoing_commitment.astype(float).sum()
        else:
            total_commitment = None
        total_disbursed = df_tipo3['value'].astype(float).sum() if not df_tipo3.empty else 0
        if total_commitment and total_commitment > 0:
            pct = 100 * total_disbursed / total_commitment
            st.metric("% Desembolsado respecto a compromiso/aprobación", f"{pct:.1f}%")
            st.markdown(f'''
                <div style="width: 40%; min-width:120px; max-width:320px; margin: 0 auto 1.2rem 0; height: 22px; background: #f5f5f5; border-radius: 11px; overflow: hidden; border: 1px solid #eee;">
                    <div style="height: 100%; width: {pct:.2f}%; background: linear-gradient(90deg, #43ea7f 0%, #1db954 100%); float: left;"></div>
                    <div style="height: 100%; width: {100-pct:.2f}%; background: linear-gradient(90deg, #ff4b4b 0%, #cc0407 100%); float: left;"></div>
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No se encontró un valor de 'outgoing commitment' (tipo 2) para calcular el porcentaje de desembolso.")
        if not df_sel.empty:
            # Solo transacciones tipo 3 para curva y tabla
            if not df_tipo3.empty:
                df_tipo3['transaction-date'] = pd.to_datetime(df_tipo3['transaction-date/@iso-date'])
                df_tipo3 = df_tipo3.sort_values('transaction-date')
                df_tipo3['acumulado'] = df_tipo3['value'].cumsum()
                # Tooltip personalizado
                hover_data = {
                    'transaction-date': True,
                    'value': ':,.0f',
                    'acumulado': ':,.0f',
                }
                fig = px.line(
                    df_tipo3,
                    x='transaction-date',
                    y='acumulado',
                    markers=True,
                    title=f"Curva de desembolsos - {selected_id}",
                    hover_data=hover_data,
                    line_shape='linear',
                )
                fig.update_traces(line_color='#cc0407', marker_color='#cc0407')
                fig.update_layout(title={'x':0.5, 'xanchor':'center'})
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(showgrid=False)
                # Tabla sin decimales
                df_tabla = df_tipo3[['transaction-date', 'value', 'acumulado']].copy()
                # Formatear la fecha para que no muestre la hora
                df_tabla['transaction-date'] = df_tabla['transaction-date'].dt.strftime('%Y-%m-%d')
                df_tabla['value'] = df_tabla['value'].astype(float).round(0).apply(lambda x: f"{int(x):,}").str.replace(",", ".")
                df_tabla['acumulado'] = df_tabla['acumulado'].astype(float).round(0).apply(lambda x: f"{int(x):,}").str.replace(",", ".")
                col1, col2 = st.columns([1.1, 1.9])
                chart_height = 420  # Altura fija para ambos
                with col1:
                    st.dataframe(df_tabla, height=chart_height, hide_index=True)
                with col2:
                    st.plotly_chart(fig, use_container_width=True, height=chart_height)
            else:
                st.info("No hay transacciones de tipo 3 para este proyecto.")
        else:
            st.info("No hay transacciones para este proyecto.")
    else:
        st.info("Primero sube un archivo Excel en la primera página.")

elif page == "Validar XML IATI":
    st.header("Validar archivo XML contra estándar IATI (estricto)")
    uploaded_xml = st.file_uploader("Sube tu archivo XML IATI", type=["xml"])
    if uploaded_xml:
        # Cargar el esquema XSD oficial de IATI 2.03
        xsd_path = os.path.join(os.path.dirname(__file__), 'iati-activities-schema.xsd')
        try:
            schema = xmlschema.XMLSchema(xsd_path)
        except Exception as ex:
            st.error(f"Error cargando el esquema XSD: {ex}")
            st.stop()
        # Leer el XML subido
        try:
            xml_bytes = uploaded_xml.read()
            # Validar el XML
            is_valid = schema.is_valid(xml_bytes)
            if is_valid:
                st.success("¡El archivo XML es válido según el estándar IATI 2.03!")
            else:
                st.error("El archivo XML NO es válido según el estándar IATI 2.03. Errores:")
                for error in schema.iter_errors(xml_bytes):
                    # Intenta obtener la posición si existe, si no, solo muestra el mensaje
                    pos = getattr(error, "position", None)
                    if pos:
                        st.write(f"- Línea {pos[0]}, columna {pos[1]}: {error.message}")
                    else:
                        st.write(f"- {error.message}")
        except Exception as ex:
            st.error(f"Error al procesar el XML: {ex}")
    else:
        st.info("Por favor, sube un archivo XML para validar.")
