// Exporta, em JSON no stdout, o conteudo estatico do painel que vira fichas de fundamentos
// (TASK-IA-09): glossario basico, glossario academico, padroes de velas, formulas por tema e os cursos
// (cada um ligado a um PDF de estudo, com paginas, objetivo e topicos por aula).
// So le os modulos do painel (nada e alterado la). Uso:
//   node scripts/exportar_painel.mjs ../painel-ativos-frontend > var/painel.json
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const painel = resolve(process.argv[2] || '../painel-ativos-frontend');
const js = join(painel, 'public', 'js');

// Os modulos de pagina definem Web Components ao serem importados: dubles minimos bastam.
globalThis.HTMLElement = class {};
globalThis.customElements = { define() {}, get() {} };
globalThis.window = { location: { hash: '' }, addEventListener() {} };
globalThis.document = { querySelector: () => null, addEventListener() {} };

/** TEMAS nao e exportado: copia o modulo para uma pasta temporaria exportando-o, com imports absolutos. */
async function temasDasFormulas() {
  const origem = join(js, 'pages', 'FormulasPage.js');
  const texto = readFileSync(origem, 'utf8')
    .replace(/^const TEMAS = /m, 'export const TEMAS = ')
    .replace(/from '(\.\.?\/[^']+)'/g, (_, rel) => `from '${pathToFileURL(resolve(dirname(origem), rel)).href}'`);
  const pasta = mkdtempSync(join(tmpdir(), 'formulas-'));
  try {
    const copia = join(pasta, 'FormulasPage.mjs');
    writeFileSync(copia, texto);
    return (await import(pathToFileURL(copia).href)).TEMAS;
  } finally {
    rmSync(pasta, { recursive: true, force: true });
  }
}

const importar = (rel) => import(pathToFileURL(join(js, rel)).href);
const { GLOSSARIO } = await importar('pages/GlossarioPage.js');
const { glossarioAcademico } = await importar('estudos/glossarioAcademico.js');
const { PADROES_DETALHADOS } = await importar('estudos/glossarioPadroes.js');
const { cursos } = await importar('estudos/cursos.js');
const formulas = await temasDasFormulas();

if (!formulas) throw new Error('TEMAS nao encontrado em FormulasPage.js');
process.stdout.write(JSON.stringify({
  glossario: GLOSSARIO, academico: glossarioAcademico, padroes: PADROES_DETALHADOS, formulas, cursos,
}));
