using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using BackendNet.Models;
using BackendNet.Services;
using System.Security.Claims;
using System.Threading.Tasks;
using System.Collections.Generic;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [Authorize]
    public class WorkspaceController : ControllerBase
    {
        private readonly IWorkspaceService _workspaceService;

        public WorkspaceController(IWorkspaceService workspaceService)
        {
            _workspaceService = workspaceService;
        }

        [HttpPost]
        public async Task<ActionResult<Workspace>> CreateWorkspace([FromBody] CreateWorkspaceRequest req)
        {
            var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userId))
            {
                userId = User.FindFirst(ClaimTypes.Name)?.Value;
            }

            if (string.IsNullOrEmpty(userId))
            {
                return Unauthorized(new { error = "User identifier claim not found in JWT token." });
            }

            var workspace = await _workspaceService.CreateWorkspaceAsync(req.Name, req.Description, userId, req.WorkspaceId);
            return Ok(workspace);
        }

        [HttpGet("{workspaceId}")]
        public async Task<ActionResult<Workspace>> GetWorkspace(string workspaceId)
        {
            var workspace = await _workspaceService.GetWorkspaceAsync(workspaceId);
            if (workspace == null)
            {
                return NotFound(new { error = $"Workspace {workspaceId} not found." });
            }
            return Ok(workspace);
        }

        [HttpPost("{workspaceId}/draft")]
        public async Task<ActionResult<ProposalVersion>> SaveDraft(string workspaceId, [FromBody] SaveDraftRequest req)
        {
            var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userId))
            {
                userId = User.FindFirst(ClaimTypes.Name)?.Value;
            }

            if (string.IsNullOrEmpty(userId))
            {
                return Unauthorized(new { error = "User identifier claim not found in JWT token." });
            }

            var version = await _workspaceService.SaveDraftAsync(workspaceId, req.Content, userId, req.Comment);
            return Ok(version);
        }

        [HttpGet("{workspaceId}/versions")]
        public async Task<ActionResult<List<ProposalVersion>>> GetVersionHistory(string workspaceId)
        {
            var versions = await _workspaceService.GetVersionHistoryAsync(workspaceId);
            return Ok(versions);
        }

        [HttpGet("version/{versionId}")]
        public async Task<ActionResult<ProposalVersion>> GetVersion(string versionId)
        {
            try
            {
                var version = await _workspaceService.GetVersionAsync(versionId);
                return Ok(version);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(new { error = ex.Message });
            }
        }

        [HttpGet("{workspaceId}/export")]
        public async Task<IActionResult> ExportProposal(string workspaceId, [FromQuery] string format = "pdf")
        {
            var url = await _workspaceService.ExportProposalAsync(workspaceId, format);
            if (string.IsNullOrEmpty(url)) return NotFound(new { error = "No content available to export or workspace not found." });
            return Ok(new { downloadUrl = url });
        }

        [HttpPost("{workspaceId}/invite")]
        public async Task<IActionResult> InviteMember(string workspaceId, [FromBody] InviteRequest req)
        {
            var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            if (string.IsNullOrEmpty(userId))
            {
                userId = User.FindFirst(ClaimTypes.Name)?.Value;
            }

            if (string.IsNullOrEmpty(userId))
            {
                return Unauthorized(new { error = "User identifier claim not found in JWT token." });
            }

            await _workspaceService.InviteMemberAsync(workspaceId, req.Email, req.Role, userId);
            return Ok(new { message = "Invitation processed successfully" });
        }
    }

    public class CreateWorkspaceRequest
    {
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string? WorkspaceId { get; set; }
    }

    public class SaveDraftRequest
    {
        public string Content { get; set; } = string.Empty;
        public string Comment { get; set; } = string.Empty;
    }

    public class InviteRequest
    {
        public string Email { get; set; } = string.Empty;
        public string Role { get; set; } = string.Empty; // "Admin", "Editor", "Viewer", "ComplianceOfficer"
    }
}
