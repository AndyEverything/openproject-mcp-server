# Deployment Checklist - FastMCP Cloud

Sử dụng checklist này để đảm bảo deploy thành công lên FastMCP Cloud.

## Pre-Deployment Checklist

### Code & Configuration

- [ ] Code đã được test kỹ trên local
- [ ] Tất cả tests đã pass (nếu có)
- [ ] Dependencies đã được update trong `pyproject.toml`
- [ ] File `.fastmcp.yaml` đã được cấu hình đúng
- [ ] File `.env.example` đã được update với tất cả biến cần thiết
- [ ] Không có file `.env` thật trong git (check `.gitignore`)
- [ ] README.md đã có hướng dẫn đầy đủ

### Security

- [ ] API keys không được hardcode trong code
- [ ] Tất cả secrets sẽ được config qua environment variables
- [ ] File `.gitignore` chứa `.env` và các file sensitive khác
- [ ] Không có credentials trong git history
- [ ] Permissions được kiểm tra trên OpenProject instance

### Testing

- [ ] Test với stdio transport local: `uv run python openproject-mcp-fastmcp.py`
- [ ] Test với SSE transport local: `uv run python openproject-mcp-sse.py`
- [ ] Test tất cả 40 tools hoạt động đúng
- [ ] Test connection với OpenProject API
- [ ] Test proxy settings (nếu có)

## Deployment Checklist

### Initial Setup

- [ ] Đã có tài khoản FastMCP Cloud
- [ ] FastMCP CLI đã được cài đặt: `pip install fastmcp-cli`
- [ ] Đã login: `fastmcp login`
- [ ] Dependencies đã sync: `uv sync`

### Deploy

- [ ] Run: `fastmcp deploy`
- [ ] Deployment thành công (không có errors)
- [ ] Note lại deployment URL được cung cấp
- [ ] Note lại deployment ID/version

### Post-Deployment Configuration

- [ ] Truy cập FastMCP Cloud dashboard
- [ ] Tìm project "openproject-mcp"
- [ ] Vào Settings > Environment Variables
- [ ] Configure các biến:
  - [ ] `OPENPROJECT_URL` = https://your-openproject.com
  - [ ] `OPENPROJECT_API_KEY` = your-api-key-here
  - [ ] `OPENPROJECT_PROXY` = http://proxy:3128 (nếu có)
  - [ ] `LOG_LEVEL` = INFO
  - [ ] `TEST_CONNECTION_ON_STARTUP` = false (hoặc true để debug)
- [ ] Save environment variables
- [ ] Restart server sau khi config

### Verification

- [ ] Server status là "Running": `fastmcp status openproject-mcp`
- [ ] Health check pass: Check dashboard hoặc `curl https://your-org.fastmcp.cloud/openproject-mcp/health`
- [ ] Logs không có errors: `fastmcp logs openproject-mcp --level ERROR`
- [ ] Test connection từ một client:
  - [ ] Configure Claude Desktop với SSE URL
  - [ ] Restart Claude Desktop
  - [ ] Test tool: "Test connection to OpenProject"
  - [ ] Test một vài tools khác (list projects, list work packages)

### Monitoring Setup

- [ ] Enable alerts cho high error rate
- [ ] Enable alerts cho high latency
- [ ] Enable alerts cho resource usage >80%
- [ ] Configure notification channels (email/Slack)
- [ ] Test alerts bằng cách trigger một error

## User Rollout Checklist

### Documentation

- [ ] Chuẩn bị hướng dẫn cho users:
  - [ ] [HUONG_DAN_KET_NOI_CLOUD.md](HUONG_DAN_KET_NOI_CLOUD.md) (tiếng Việt)
  - [ ] [FASTMCP_CLOUD_DEPLOYMENT.md](FASTMCP_CLOUD_DEPLOYMENT.md) (English)
  - [ ] [QUICK_START_CLOUD.md](QUICK_START_CLOUD.md)
- [ ] Tạo internal wiki/docs page
- [ ] Tạo FAQ document

### Communication

- [ ] Thông báo cho users về MCP server mới
- [ ] Share connection URL
- [ ] Share hướng dẫn kết nối
- [ ] Announce support channels (Slack, email)
- [ ] Schedule training session (optional)

### Access Management

- [ ] Invite team members vào FastMCP Cloud dashboard (nếu cần)
- [ ] Assign roles (Admin, Developer, User)
- [ ] Generate API keys cho users (nếu cần per-user access)
- [ ] Document access control policies

### Support Preparation

- [ ] Create Slack channel: #openproject-mcp-support
- [ ] Assign support team members
- [ ] Prepare common troubleshooting responses
- [ ] Test support workflow

## Post-Deployment Monitoring (First Week)

### Daily Checks

- [ ] Day 1: Check logs for errors every 2 hours
- [ ] Day 1: Monitor request volume and latency
- [ ] Day 2-3: Check error rates and user feedback
- [ ] Day 4-7: Review performance metrics
- [ ] Week 1 end: Review all metrics and adjust resources if needed

### Metrics to Monitor

- [ ] Total requests per day
- [ ] Average latency
- [ ] Error rate (should be <1%)
- [ ] Resource usage (CPU, memory)
- [ ] Number of active users
- [ ] Most used tools

### User Feedback

- [ ] Collect feedback qua Slack/email
- [ ] Track common issues
- [ ] Update FAQ based on questions
- [ ] Note feature requests

## Rollback Plan

Prepare rollback plan in case of issues:

- [ ] Know how to rollback: `fastmcp rollback openproject-mcp --version <previous-version-id>`
- [ ] List all deployments: `fastmcp deployments list`
- [ ] Document current version ID
- [ ] Test rollback procedure in staging (if available)
- [ ] Have contact info for FastMCP support

## Emergency Contacts

- **FastMCP Cloud Support**: support@fastmcp.cloud
- **Internal Admin**: [Your name/email]
- **OpenProject Admin**: [Admin name/email]
- **Slack Channel**: #openproject-mcp-support

## Maintenance Schedule

### Weekly

- [ ] Review error logs
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Update documentation if needed

### Monthly

- [ ] Review and rotate API keys if needed
- [ ] Update dependencies: `uv sync --upgrade`
- [ ] Re-deploy if dependencies updated
- [ ] Review resource allocation and adjust if needed
- [ ] Archive old logs

### Quarterly

- [ ] Security audit
- [ ] Performance review and optimization
- [ ] User satisfaction survey
- [ ] Review and update documentation

## Success Criteria

Deployment is considered successful when:

- [ ] Server uptime >99.5%
- [ ] Error rate <1%
- [ ] Average latency <500ms
- [ ] All 40 tools working correctly
- [ ] At least 5 active users
- [ ] No critical issues reported
- [ ] User satisfaction score >4/5

---

**Last Updated**: 2025-01-XX
**Version**: 1.0
**Reviewed By**: [Your name]
