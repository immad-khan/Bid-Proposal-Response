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
    public class DashboardController : ControllerBase
    {
        private readonly IDashboardService _dashboardService;

        public DashboardController(IDashboardService dashboardService)
        {
            _dashboardService = dashboardService;
        }

        [HttpGet("win-probability")]
        public async Task<ActionResult<List<WinProbabilityDto>>> GetWinProbability()
        {
            var userId = User.FindFirst(ClaimTypes.NameIdentifier)?.Value;
            // Fallback for testing/simple setups: if userId is not in ClaimTypes.NameIdentifier, try ClaimTypes.Name
            if (string.IsNullOrEmpty(userId))
            {
                userId = User.FindFirst(ClaimTypes.Name)?.Value;
            }

            if (string.IsNullOrEmpty(userId))
            {
                return Unauthorized(new { error = "User identifier claim not found in JWT token." });
            }

            var data = await _dashboardService.GetWinProbabilitiesAsync(userId);
            return Ok(data);
        }

        [HttpGet("analysis/{projectId}")]
        public async Task<ActionResult<WinProbabilityDetailDto>> GetDetailedAnalysis(string projectId)
        {
            try
            {
                var detail = await _dashboardService.GetDetailedAnalysisAsync(projectId);
                return Ok(detail);
            }
            catch (KeyNotFoundException ex)
            {
                return NotFound(new { error = ex.Message });
            }
        }
    }
}
