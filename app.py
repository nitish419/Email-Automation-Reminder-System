import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()
SENDER_EMAIL = os.getenv("EMAIL_SENDER")
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Email Automation & Reminder System", page_icon="📧", layout="wide")

# --- 3D BACKGROUND ILLUSION ---
three_js_illusion = """
<!DOCTYPE html>
<html>
<head>
<style>
    body { margin: 0; background-color: transparent; overflow: hidden; }
    canvas { display: block; width: 100%; height: 350px; }
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
</head>
<body>
<script>
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 350, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({alpha: true, antialias: true});
    renderer.setSize(window.innerWidth, 350);
    document.body.appendChild(renderer.domElement);

    const geometry = new THREE.TorusKnotGeometry(10, 2.5, 120, 16);
    const material = new THREE.MeshBasicMaterial({ color: 0x00e5ff, wireframe: true, transparent: true, opacity: 0.3 });
    const shape = new THREE.Mesh(geometry, material);
    scene.add(shape);

    camera.position.z = 25;

    function animate() {
        requestAnimationFrame(animate);
        shape.rotation.x += 0.005;
        shape.rotation.y += 0.01;
        shape.rotation.z += 0.002;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / 350;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, 350);
    });
</script>
</body>
</html>
"""
components.html(three_js_illusion, height=350)

# --- CSS STYLING ---
st.markdown("""
<style>
    .glow-header { font-size: 50px; font-weight: 900; color: #ffffff; text-align: center; text-shadow: 0 0 20px #000000, 0 0 10px #00e5ff; margin-top: -250px; position: relative; z-index: 10; }
    .sub-header { text-align: center; color: #e0e0e0; margin-bottom: 40px; font-size: 18px; position: relative; z-index: 10; text-shadow: 0 0 5px #000000; }
    .preview-box { background-color: #1e1e1e; color: #ffffff; padding: 20px; border-radius: 8px; border-left: 5px solid #00e5ff; font-family: sans-serif; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="glow-header">Email Automation & Reminder System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Dynamic Template Dispatcher</div>', unsafe_allow_html=True)
st.write("\n" * 5)

# --- DYNAMIC CONTROL PANEL ---
col1, col2 = st.columns([1, 1.2]) # Split screen into inputs (left) and preview (right)

with col1:
    st.subheader("1. Recipient Details")
    recipient_email = st.text_input("Target Email Address:", placeholder="e.g., student@university.edu")
    recipient_name = st.text_input("Recipient Name:", placeholder="e.g., Alex")
    
    st.subheader("2. Message Configuration")
    subject_line = st.text_input("Email Subject Line:", placeholder="e.g., Important Account Update")
    selected_template = st.selectbox("Select Automation Template:", ("money", "book", "meeting"))
    
    st.subheader("3. Dynamic Variables")
    # Store variables in a dictionary to format the template later
    custom_data = {"Name": recipient_name if recipient_name else "[Name]"}
    
    if selected_template == "money":
        custom_data['Amount'] = st.text_input("Fee Amount (Rs):", value="500")
        custom_data['DueDate'] = st.text_input("Due Date:", value="2026-05-15")
            
    elif selected_template == "book":
        custom_data['BookName'] = st.text_input("Name of Book:", value="Python Crash Course")
        custom_data['DueDate'] = st.text_input("Return Date:", value="2026-05-20")
            
    elif selected_template == "meeting":
        custom_data['MeetingTime'] = st.text_input("Time of Meeting:", value="10:00 AM")
        custom_data['DueDate'] = st.text_input("Meeting Date:", value="2026-05-10")
        
    st.write("")
    dry_run_mode = st.toggle("Enable DRY RUN (Test without sending)", value=True)

with col2:
    st.subheader("📧 Live Email Preview")
    
    # Load and format the template in real-time
    template_filepath = f"templates/{selected_template}.txt"
    try:
        with open(template_filepath, 'r', encoding='utf-8') as file:
            raw_template = file.read()
            
        # Dynamically inject the user's typed variables into the text
        try:
            live_preview_text = raw_template.format(**custom_data)
        except KeyError as e:
            live_preview_text = f"Waiting for input... Template needs the variable: {e}"
            
    except FileNotFoundError:
        live_preview_text = f"Error: Could not find {template_filepath} in your templates folder."

    # Show the exact email that will be sent
    st.markdown(f'<div class="preview-box"><strong>Subject:</strong> {subject_line if subject_line else "[Subject]"}<br><br>{live_preview_text}</div>', unsafe_allow_html=True)
    
    st.write("")
    execute_btn = st.button("🚀 SEND THIS EMAIL", type="primary", use_container_width=True)

# --- EXECUTION LOGIC ---
if execute_btn:
    if not recipient_email or not subject_line:
        st.error("⚠️ Error: Target Email and Subject Line are required!")
    else:
        with st.spinner("Connecting to mail server..."):
            if dry_run_mode:
                st.success(f"✅ DRY RUN SUCCESS: Email successfully generated for {recipient_email}. (No actual email sent due to Safe Mode).")
            else:
                try:
                    # Authenticate and Send
                    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                    
                    msg = EmailMessage()
                    msg['Subject'] = subject_line
                    msg['From'] = SENDER_EMAIL
                    msg['To'] = recipient_email
                    msg.set_content(live_preview_text)
                    
                    server.send_message(msg)
                    server.quit()
                    
                    st.success(f"✅ SUCCESS: Email successfully delivered to {recipient_email}!")
                    st.balloons()
                    
                except smtplib.SMTPAuthenticationError:
                    st.error("🚨 AUTHENTICATION FAILED: Google rejected your password. Ensure you are using a 16-digit 'App Password' in your .env file, not your normal password.")
                except Exception as e:
                    st.error(f"🚨 FAILED TO SEND: {str(e)}")