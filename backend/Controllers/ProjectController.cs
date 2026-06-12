using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using BackendNet.Services;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ProjectController : ControllerBase
    {
        private readonly IProjectManagementService _projectManagementService;

        public ProjectController(IProjectManagementService projectManagementService)
        {
            _projectManagementService = projectManagementService;
        }

        [HttpGet]
        public async Task<IActionResult> GetProjects()
        {
            var projects = await _projectManagementService.GetProjectsAsync();
            return Ok(projects);
        }

        [HttpGet("{id}")]
        public async Task<IActionResult> GetProjectById(string id)
        {
            var project = await _projectManagementService.GetProjectByIdAsync(id);
            if (project == null)
            {
                return NotFound(new { error = $"Project {id} not found." });
            }
            return Ok(project);
        }
    }
}
