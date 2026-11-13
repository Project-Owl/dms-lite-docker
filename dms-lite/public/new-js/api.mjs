export async function fetchJson(path,options = {}) {
  const response = await fetch(path,{...options,signal:options.signal || AbortSignal.timeout(5000)});
  if (!response.ok) throw new Error('Request failed.');
  return response.json();
}
export function showFailure(element,retry) {
  element.replaceChildren(document.createTextNode('Could not load data. '));
  const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Retry';
  button.addEventListener('click',retry); element.append(button);
}
export function appendRow(body,values) {
  const row = body.insertRow();
  for (const value of values) row.insertCell().textContent = value ?? '';
}
