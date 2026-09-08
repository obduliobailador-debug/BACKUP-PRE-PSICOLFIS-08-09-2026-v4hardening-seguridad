import { usePageSeo } from "../lib/seo";

export const LegalPage = () => {
  usePageSeo({
    title: 'Aviso Legal y Política de Privacidad · PSICOLFIS.NET',
    description: 'Información legal, política de privacidad y uso de cookies de PSICOLFIS.NET — servicio de agentes de IA personalizados.',
    canonicalPath: '/legal',
  });
  return (
    <div className="legal-page">
      <div className="legal-container">
        <div className="legal-header">
          <a href="/" className="back-link">← Volver al inicio</a>
          <h1>Aviso Legal y Política de Privacidad</h1>
        </div>

        <div className="legal-content">
          <section id="aviso-legal">
            <h2>Aviso Legal</h2>
            
            <h3>1. Datos Identificativos</h3>
            <p>
              En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de Servicios de la Sociedad de la Información y de Comercio Electrónico, se informa que:
            </p>
            <ul>
              <li><strong>Denominación social:</strong> PSICOLFIS.NET</li>
              <li><strong>Domicilio:</strong> España</li>
              <li><strong>Correo electrónico:</strong> obdulio@psicolfis.net</li>
              <li><strong>Sitio web:</strong> psicolfis.net</li>
            </ul>

            <h3>2. Objeto</h3>
            <p>
              El presente aviso legal regula el uso del sitio web psicolfis.net, propiedad de PSICOLFIS.NET, que pone a disposición de los usuarios de Internet sus servicios de consultoría en inteligencia artificial y desarrollo de agentes personalizados.
            </p>

            <h3>3. Condiciones de Uso</h3>
            <p>
              El acceso y uso de este sitio web implica la aceptación plena de las presentes condiciones generales. Si no está de acuerdo con estas condiciones, no debe usar este sitio web.
            </p>

            <h3>4. Responsabilidad</h3>
            <p>
              PSICOLFIS.NET no se hace responsable de los daños y perjuicios que pudieran derivarse del uso incorrecto de este sitio web. El usuario es el único responsable del uso que haga de los contenidos y servicios ofrecidos.
            </p>
          </section>

          <section id="privacidad">
            <h2>Política de Privacidad</h2>
            
            <h3>1. Responsable del Tratamiento</h3>
            <p>
              <strong>PSICOLFIS.NET</strong> es el responsable del tratamiento de los datos personales del Usuario y le informa que estos datos serán tratados de conformidad con lo dispuesto en el Reglamento (UE) 2016/679 de 27 de abril de 2016 (GDPR) relativo a la protección de las personas físicas en lo que respecta al tratamiento de datos personales y a la libre circulación de estos datos.
            </p>

            <h3>2. Finalidad del Tratamiento</h3>
            <p>Los datos personales se tratarán para las siguientes finalidades:</p>
            <ul>
              <li>Gestión de consultas y solicitudes de información</li>
              <li>Prestación de servicios de consultoría en IA</li>
              <li>Procesamiento de pagos y facturación</li>
              <li>Comunicaciones comerciales (con consentimiento previo)</li>
            </ul>

            <h3>3. Legitimación</h3>
            <p>
              La base legal para el tratamiento de sus datos es el consentimiento del interesado, la ejecución de un contrato o la aplicación de medidas precontractuales.
            </p>

            <h3>4. Conservación de Datos</h3>
            <p>
              Los datos se conservarán durante el tiempo necesario para cumplir con la finalidad para la que se recabaron y para determinar las posibles responsabilidades que se pudieran derivar de dicha finalidad y del tratamiento de los datos.
            </p>

            <h3>5. Derechos del Usuario</h3>
            <p>El Usuario tiene derecho a:</p>
            <ul>
              <li>Solicitar el acceso a los datos personales</li>
              <li>Solicitar su rectificación o supresión</li>
              <li>Solicitar la limitación de su tratamiento</li>
              <li>Oponerse al tratamiento</li>
              <li>Solicitar la portabilidad de los datos</li>
            </ul>
            <p>
              Para ejercer estos derechos, puede contactar con nosotros en: <strong>obdulio@psicolfis.net</strong>
            </p>
          </section>

          <section id="cookies">
            <h2>Política de Cookies</h2>
            
            <h3>¿Qué son las cookies?</h3>
            <p>
              Las cookies son pequeños archivos de texto que se almacenan en su dispositivo cuando visita un sitio web. Nos ayudan a mejorar su experiencia de navegación y a analizar el uso del sitio.
            </p>

            <h3>Tipos de cookies que utilizamos:</h3>
            <ul>
              <li><strong>Cookies técnicas:</strong> Necesarias para el funcionamiento del sitio web</li>
              <li><strong>Cookies analíticas:</strong> Para analizar el comportamiento de los usuarios</li>
              <li><strong>Cookies de personalización:</strong> Para recordar sus preferencias</li>
            </ul>

            <h3>Gestión de cookies</h3>
            <p>
              Puede configurar su navegador para rechazar las cookies o para que le avise cuando se envíen cookies. Sin embargo, si rechaza las cookies, es posible que no pueda utilizar todas las funciones de nuestro sitio web.
            </p>
          </section>

          <div className="legal-contact">
            <h3>Contacto</h3>
            <p>
              Para cualquier consulta relacionada con este aviso legal o política de privacidad, puede contactarnos en:
            </p>
            <p><strong>Email:</strong> obdulio@psicolfis.net</p>
            <p><strong>Última actualización:</strong> Diciembre 2024</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Página privada para clientes que han comprado un agente.
// Valida el JWT recibido en la URL contra el backend y embebe el agente
// de Pickaxe correcto sin que el cliente tenga que salir de psicolfis.net.
