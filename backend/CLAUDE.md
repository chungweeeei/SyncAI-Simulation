# Project Overview
 
NestJS 後端 API 專案，使用 TypeScript 開發。
 
## Tech Stack
 
- **Runtime**: Node.js + NestJS
- **Language**: TypeScript (strict mode)
- **ORM**: TypeORM
- **Database**: PostgreSQL
- **Validation**: class-validator + class-transformer
- **Testing**: Jest
- **API Docs**: Swagger (@nestjs/swagger)
 
## Commands
 
```bash
npm run start:dev          # 啟動開發環境 (hot reload)
npm run build              # 編譯專案
npm run start:prod         # 啟動 production
npm run test               # 執行單元測試
npm run test:e2e           # 執行 E2E 測試
npm run test:cov           # 測試覆蓋率報告
npm run lint               # ESLint 檢查
npm run format             # Prettier 格式化
npm run migration:generate # 產生 migration
npm run migration:run      # 執行 migration
```
 
## Architecture
 
```
src/
├── main.ts                 # 程式進入點，bootstrap
├── app.module.ts           # Root module
├── common/                 # 共用工具：guards, interceptors, filters, decorators, pipes
├── config/                 # 環境設定 (ConfigModule)
├── modules/                # 功能模組，每個模組包含 controller, service, dto, entity
│   └── <module-name>/
│       ├── <name>.module.ts
│       ├── <name>.controller.ts
│       ├── <name>.service.ts
│       ├── dto/
│       ├── entities/
│       └── __tests__/
├── database/               # Migration 檔案與 seed
└── shared/                 # 跨模組共用的 interfaces, enums, constants
```
 
## Code Style
 
- 使用 NestJS 的 DI（依賴注入）模式，所有 service 都必須透過 constructor injection
- DTO 使用 class-validator decorators 做驗證，禁止在 controller 內手動驗證
- Entity 與 DTO 分離，不直接回傳 entity 給 client
- 每個 module 自包含，避免跨 module 直接 import service（應透過 exports）
- 統一使用 async/await，不使用 .then() chain
- 使用 named exports，不使用 default export
- 檔名格式：`kebab-case`（例如 `user-profile.service.ts`）
- Interface / Type 放在 shared/ 或各模組的 dto/ 資料夾
 
## Error Handling
 
- 使用 NestJS 內建 HttpException 及其子類別（BadRequestException, NotFoundException 等）
- 全域 ExceptionFilter 統一處理未預期的錯誤，回傳格式：`{ statusCode, message, error, timestamp }`
- 業務邏輯的錯誤在 service 層拋出，controller 不做 try-catch（由 filter 處理）
 
## API Conventions
 
- RESTful 命名：`GET /users`, `POST /users`, `GET /users/:id`, `PATCH /users/:id`, `DELETE /users/:id`
- Response 統一封裝格式：`{ data, meta?, message? }`
- Pagination 使用 query params：`?page=1&limit=20`，回傳 meta 包含 total, page, limit
- 版本控制使用 URI prefix：`/api/v1/`
 
## Testing
 
- 單元測試放在各模組的 `__tests__/` 資料夾，檔名 `*.spec.ts`
- E2E 測試放在 `test/` 根目錄，檔名 `*.e2e-spec.ts`
- Service 測試 mock 掉 repository，Controller 測試 mock 掉 service
- 修改或新增 feature 後，務必執行 `npm run test` 確認不影響既有功能
 
## Important Notes
 
- 禁止提交 `.env` 檔案，環境變數透過 ConfigModule + `.env.example` 管理
- Database credentials 和 JWT secret 必須從環境變數讀取，禁止 hardcode
- 所有 migration 必須可以 revert（撰寫 down method）
- 新增模組時，確認已在 AppModule 或對應的 parent module 中 import
- Circular dependency 是常見問題，使用 `forwardRef()` 解決，但優先考慮重構拆分
 
## Git Workflow
 
- Branch 命名：`feature/<name>`, `fix/<name>`, `refactor/<name>`
- Commit 使用 conventional commits 格式：`feat:`, `fix:`, `refactor:`, `test:`, `docs:`
- 每次開新功能前先開新 branch，不直接在 main 上開發
 
## When Compacting
 
當 context 壓縮時，保留以下資訊：
- 目前正在修改的檔案清單
- 已完成和待完成的任務
- 遇到的錯誤與解決方案
- 資料庫 schema 的變更紀錄