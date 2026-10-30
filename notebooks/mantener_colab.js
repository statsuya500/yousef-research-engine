// Pega esto en la consola del navegador (F12 → Console) con la pestaña de Colab abierta.
// Evita que Colab desconecte la sesión por inactividad mientras descarga o genera.
function mantenerColab() {
  const boton = document.querySelector("colab-connect-button");
  const conectar = boton && boton.shadowRoot && boton.shadowRoot.querySelector("#connect");
  if (conectar) conectar.click();
  else document.querySelector("#top-toolbar")?.click();
  console.log("Colab sigue activo:", new Date().toLocaleTimeString());
}
const vigilante = setInterval(mantenerColab, 60 * 1000);
// Para pararlo: clearInterval(vigilante)
