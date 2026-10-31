// Light/dark preference. A saved choice wins; otherwise follow the device setting.
export const THEME_KEY='defectrag-theme';
export function initialTheme(storage=globalThis.localStorage,media=globalThis.matchMedia){
 try{const saved=storage?.getItem(THEME_KEY);if(saved==='light'||saved==='dark')return saved}catch{}
 try{return media?.('(prefers-color-scheme: dark)').matches?'dark':'light'}catch{return 'light'}
}
export function applyTheme(theme,root=globalThis.document?.documentElement,storage=globalThis.localStorage){
 root?.classList.toggle('dark',theme==='dark');
 try{storage?.setItem(THEME_KEY,theme)}catch{}
}
