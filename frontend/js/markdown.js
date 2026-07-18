/**
 * Renderizador de markdown básico a HTML seguro.
 * Cubre: encabezados (## ###), negrita/cursiva, código inline y en bloque,
 * listas con '-', y tablas simples (| col | col |).
 * No soporta LaTeX/matemáticas — mismo alcance que el PDF del backend.
 */
function renderMarkdown(text) {
    if (!text) return '';

    // Escapa HTML antes de aplicar markdown, para evitar inyección de tags
    let escaped = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    const lines = escaped.split('\n');
    let html = '';
    let inCodeBlock = false;
    let codeBuffer = [];
    let inList = false;
    let i = 0;

    const inlineFormat = (line) => {
        line = line.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        line = line.replace(/(?<!\*)\*(?!\*)(.+?)\*(?!\*)/g, '<em>$1</em>');
        line = line.replace(/`(.+?)`/g, '<code class="px-1 py-0.5 rounded bg-[var(--line)] text-xs">$1</code>');
        return line;
    };

    while (i < lines.length) {
        const line = lines[i];

        // Bloque de código
        if (line.trim().startsWith('```')) {
            if (!inCodeBlock) {
                inCodeBlock = true;
                codeBuffer = [];
            } else {
                inCodeBlock = false;
                html += `<pre class="bg-[var(--paper)] border border-[var(--line)] rounded-lg p-3 text-xs font-mono overflow-x-auto mb-3">${codeBuffer.join('\n')}</pre>`;
            }
            i++;
            continue;
        }
        if (inCodeBlock) {
            codeBuffer.push(line);
            i++;
            continue;
        }

        // Tabla
        if (line.trim().startsWith('|')) {
            const rows = [];
            while (i < lines.length && lines[i].trim().startsWith('|')) {
                if (!/^\|[\s:|-]+\|$/.test(lines[i].trim())) {
                    rows.push(lines[i].trim().replace(/^\||\|$/g, '').split('|').map(c => c.trim()));
                }
                i++;
            }
            if (rows.length) {
                html += '<table class="w-full text-xs mb-3 border border-[var(--line)] rounded-lg overflow-hidden">';
                html += `<thead><tr class="bg-[var(--primary)] text-white">${rows[0].map(c => `<th class="p-2 text-left">${inlineFormat(c)}</th>`).join('')}</tr></thead>`;
                html += '<tbody>';
                rows.slice(1).forEach(r => {
                    html += `<tr class="border-t border-[var(--line)]">${r.map(c => `<td class="p-2">${inlineFormat(c)}</td>`).join('')}</tr>`;
                });
                html += '</tbody></table>';
            }
            continue;
        }

        // Encabezados
        if (line.trim().startsWith('###')) {
            html += `<h4 class="serif text-base font-semibold mt-3 mb-1" style="color:var(--secondary)">${inlineFormat(line.replace(/^#+\s*/, ''))}</h4>`;
            i++;
            continue;
        }
        if (line.trim().startsWith('##')) {
            html += `<h3 class="serif text-lg font-semibold mt-4 mb-2" style="color:var(--primary)">${inlineFormat(line.replace(/^#+\s*/, ''))}</h3>`;
            i++;
            continue;
        }

        // Listas
        if (/^\s*-\s+/.test(line)) {
            if (!inList) { html += '<ul class="list-disc pl-5 mb-2 space-y-1">'; inList = true; }
            html += `<li>${inlineFormat(line.replace(/^\s*-\s+/, ''))}</li>`;
            i++;
            continue;
        } else if (inList) {
            html += '</ul>';
            inList = false;
        }

        // Párrafo normal
        if (line.trim()) {
            html += `<p class="mb-2">${inlineFormat(line)}</p>`;
        }
        i++;
    }

    if (inList) html += '</ul>';
    return html;
}