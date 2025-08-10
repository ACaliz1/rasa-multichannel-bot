# Bot Rasa con canal personalizado para WhatsApp Cloud API
Este proyecto es una prueba de concepto de un bot desarrollado con **Rasa 2.x**, que responde de forma **diferente según el canal de origen** (en este caso, WhatsApp). El objetivo es demostrar cómo personalizar las respuestas y acciones dependiendo del canal desde el que se recibe el mensaje.
Actualmente solo está integrado con **WhatsApp**, usando el número de prueba oficial de **Meta (Facebook)** y el webhook `/webhooks/whatsapp/webhook`.
---
## Funcionalidad del bot
- Detección del canal mediante `tracker.get_latest_input_channel()`
- Respuestas simples diferenciadas por canal en `domain.yml`
- Uso de acciones personalizadas (`custom actions`)
- Canal de salida personalizado para WhatsApp (`OutputChannel`)
- Pruebas reales enviando mensajes desde el número de prueba de WhatsApp de Meta
---
## Estructura del proyecto
- `domain.yml`: contiene las respuestas por canal y el slot `canal_actual`
- `actions.py`: contiene `action_set_canal_actual`, que detecta el canal y lo guarda en el slot
- `whatsapp.py`: contiene el canal personalizado con métodos `send_text_message` y `blueprint`
- `credentials.yml`: incluye las credenciales necesarias para conectar con WhatsApp
- `endpoints.yml`: configura el endpoint para las acciones personalizadas
---
## Intents y respuestas
### Intents definidos:
- `saludo`
- `despedida`
- `preguntar_canal` (para comprobar el valor del slot `canal_actual`)
### Respuestas diferenciadas (`domain.yml`):
```yaml
utter_saludo:
 - text: "¡Hola desde whatsapp!"
   channel: whatsapp
 - text: "¡Hola desde cualquier otro canal!"
utter_despedida:
 - text: "Adiós desde whatsapp!"
   channel: whatsapp
 - text: "Adiós desde cualquier otro canal!"
utter_info_canal:
 - text: "El canal actual es: {canal_actual}"

⸻
Requisitos previos
1. Tener una cuenta en el portal de desarrolladores de Meta: https://developers.facebook.com
2. Crear una app de tipo WhatsApp en el apartado WhatsApp > Getting Started
3. Obtener los siguientes datos:
• auth_token: Token de acceso (temporal o permanente)
• phone_number_id: ID del número de prueba proporcionado por Meta
• verify_token: Cadena personalizada que usarás para verificar el webhook
4. Instalar:
• Python 3.8 o 3.9
• Rasa 2.x (pip install rasa==2.8.1 u otra versión compatible)
• Cloudflared (https://developers.cloudflare.com/cloudflared/) para exponer el webhook de forma pública
⸻
Cómo probar el bot (3 terminales)
Paso previo: activar entorno virtual
Si tienes un entorno virtual creado, actívalo:
.\venv\Scripts\activate   # En Windows
source venv/bin/activate  # En Linux/macOS
Si no tienes entorno virtual, puedes crear uno así:
python -m venv venv
Y luego instalar Rasa:
pip install rasa==2.8.1
Terminal 1 – Acciones personalizadas
rasa run actions
Terminal 2 – Servidor Rasa con API
rasa run --enable-api
Terminal 3 – Crear túnel público con Cloudflared
cloudflared tunnel --url http://localhost:5005 --protocol http2
Copia la URL generada por cloudflared (por ejemplo, https://xxxx.trycloudflare.com) y configúrala como webhook en el panel de Meta con la ruta completa:
https://xxxx.trycloudflare.com/webhooks/whatsapp/webhook

⸻
Configuración de archivos
credentials.yml
channels.whatsapp.WhatsAppInput:
 auth_token: "TU_AUTH_TOKEN"
 phone_number_id: "TU_PHONE_NUMBER_ID"
 verify_token: "TU_VERIFY_TOKEN"
endpoints.yml
action_endpoint:
 url: "http://localhost:5055/webhook"

⸻
Cómo interactuar
1. Envía un mensaje al número de prueba de WhatsApp desde tu teléfono
2. El bot responderá dependiendo del canal (en este caso, WhatsApp)
3. Puedes probar el intent preguntar_canal para recibir la respuesta con el canal actual (canal_actual)
⸻
Notas importantes
• Si usas un auth_token temporal, caduca cada 24h. Para producción, configura un token permanente desde el panel de Meta.
• Asegúrate de que la URL generada por cloudflared esté configurada correctamente como webhook.
• No es necesario volver a entrenar el bot si solo cambias el auth_token en credentials.yml.
⸻
Recursos adicionales
• Documentación oficial de Rasa: https://rasa.com/docs/
• Documentación de WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api/
• Cloudflared: https://developers.cloudflare.com/cloudflared/