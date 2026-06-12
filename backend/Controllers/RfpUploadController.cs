using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using BackendNet.Services;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class RfpUploadController : ControllerBase
    {
        private readonly IBlobStorageService _blobStorageService;
        private readonly IProjectManagementService _projectManagementService;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;
        private readonly ILogger<RfpUploadController> _logger;

        public RfpUploadController(
            IBlobStorageService blobStorageService,
            IProjectManagementService projectManagementService,
            IHttpClientFactory httpClientFactory,
            IConfiguration configuration,
            ILogger<RfpUploadController> logger)
        {
            _blobStorageService = blobStorageService;
            _projectManagementService = projectManagementService;
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
            _logger = logger;
        }

        [HttpPost("upload")]
        public async Task<IActionResult> UploadRfp(IFormFile file)
        {
            try
            {
                // Validation
                if (file == null || file.Length == 0)
                {
                    _logger.LogWarning("Upload attempted with no file");
                    return BadRequest(new { error = "No file uploaded." });
                }

                _logger.LogInformation($"Processing upload: {file.FileName} ({file.Length} bytes)");

                // 1. Upload using BlobStorageService
                string blobUrl;
                using (var stream = file.OpenReadStream())
                {
                    blobUrl = await _blobStorageService.UploadFileAsync(stream, file.FileName, file.ContentType);
                }
                _logger.LogInformation($"File uploaded successfully to: {blobUrl}");

                // 2. Create proposal project entity in local memory DB
                var projectName = Path.GetFileNameWithoutExtension(file.FileName);
                var project = await _projectManagementService.CreateProjectAsync(projectName, blobUrl);
                _logger.LogInformation($"Created proposal project: {project.Id}");

                // 3. Trigger the Python Engine (using project.Id as the Job/Tracking Id)
                var payload = new 
                { 
                    jobId = project.Id, 
                    blobUrl = blobUrl, 
                    filename = file.FileName 
                };

                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromMinutes(5);
                
                var pythonEngineUrl = _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
                
                // Let's call /parsing/parse which is our new parsing router endpoint
                _logger.LogInformation($"Triggering parser at: {pythonEngineUrl}/parsing/parse");
                var response = await client.PostAsJsonAsync($"{pythonEngineUrl}/parsing/parse", payload);

                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation($"Job {project.Id} submitted to AI engine successfully");
                    await _projectManagementService.UpdateProjectStatusAsync(project.Id, "ParsingStarted");

                    return Ok(new 
                    { 
                        status = "Success", 
                        jobId = project.Id, 
                        message = "AI Engine parsing and generation triggered.",
                        blobUrl = blobUrl 
                    });
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError($"AI Engine returned {response.StatusCode}: {errorContent}");
                    await _projectManagementService.UpdateProjectStatusAsync(project.Id, "ParsingFailed");

                    return StatusCode(500, new 
                    { 
                        error = "Failed to reach AI Engine.",
                        details = errorContent 
                    });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error during upload");
                return StatusCode(500, new { error = "An unexpected error occurred", details = ex.Message });
            }
        }
    }
}