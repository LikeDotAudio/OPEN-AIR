// ui/ lint floor — Phase 2 §3.3: only the ratchets that matter.
// 1. No NEW window.* access in converted .ts/.tsx (the bridge files below
//    are the shrinking exception list — remove entries as bridges die).
// 2. No new .jsx files (enforced by CI grep, not eslint — see contracts-ci).
// 3. No z.any() without a WHY comment (inherited from contracts review law).
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'

/** Files allowed to touch window.* — the explicit bridge list. boot.tsx
 * reads the unconverted MqttProvider/WindowManager off window until those
 * files convert; then it imports them and leaves this list. */
const WINDOW_BRIDGES = ['src/main.tsx', 'src/legacy.ts', 'src/boot.tsx']

export default tseslint.config(
  { ignores: ['dist/', 'src/legacy.ts', 'src/globals.d.ts'] },
  {
    files: ['src/**/*.{ts,tsx}', 'scripts/**/*.ts'],
    extends: [...tseslint.configs.recommended],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'no-restricted-globals': 'off',
      'no-restricted-syntax': [
        'error',
        {
          selector: "MemberExpression[object.name='window']",
          message:
            'No new window.* in converted code — import the module instead. Bridge files are listed in eslint.config.js.',
        },
      ],
    },
  },
  {
    files: WINDOW_BRIDGES,
    rules: { 'no-restricted-syntax': 'off' },
  },
)
