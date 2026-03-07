function calcularYActualizarPrecioTotal(elem) {
    const form = elem.closest('form');
    if (!form) return;

    const precioEl = form.querySelector('.precio-field');
    const cantidadEl = form.querySelector('.cantidad-field');
    const spanMostrar = form.querySelector('#precioTotal-mostrar');
    const inputHidden = form.querySelector('#precioTotal-hidden');

    const precio = parseFloat(precioEl.value) || 0;
    const cantidad = parseFloat(cantidadEl.value) || 0;
    const total = precio * cantidad;

    if (spanMostrar) spanMostrar.textContent = total.toFixed(2);
    if (inputHidden) inputHidden.value = total.toFixed(2);
}
