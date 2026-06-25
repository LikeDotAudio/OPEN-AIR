declare namespace wasm_bindgen {
    /* tslint:disable */
    /* eslint-disable */

    export function generate_panel(width: number, height: number, config_json: string): Uint8Array;

    export function generate_screw(size: number, config_json: string): Uint8Array;

    export function screw_canvas_dim(size: number): number;

}
declare type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

declare interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly generate_panel: (a: number, b: number, c: number, d: number) => [number, number];
    readonly generate_screw: (a: number, b: number, c: number) => [number, number];
    readonly screw_canvas_dim: (a: number) => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
declare function wasm_bindgen (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
