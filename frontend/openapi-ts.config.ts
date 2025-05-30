import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "./openapi.json",
  output: "./src/client",
  plugins: [
    {
      name: "@hey-api/sdk",
      // NOTE: this doesn't allow tree-shaking
      asClass: true,
      operationId: true,
    },
    {
      name: "@hey-api/client-fetch",
      runtimeConfigPath: './src/clientConfig.ts', 
    },
  ],
})
