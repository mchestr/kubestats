import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "http://localhost:8000/api/v1/openapi.json",
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
