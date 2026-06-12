using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ProposalController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;
        private readonly ILogger<ProposalController> _logger;

        public ProposalController(
            IHttpClientFactory httpClientFactory,
            IConfiguration configuration,
            ILogger<ProposalController> logger)
        {
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
            _logger = logger;
        }

        public class ProposalRequest
        {
            public string project_id { get; set; }
            public string rfp_text { get; set; }
        }

        [HttpPost("generate")]
        public async Task<IActionResult> GenerateProposal([FromBody] ProposalRequest request)
        {
            try
            {
                var pythonEngineUrl = _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromMinutes(10); // Proposal generation might take a while
                
                var payload = new 
                { 
                    projectId = request.project_id, 
                    rfpText = request.rfp_text 
                };

                _logger.LogInformation($"Proxying proposal generation to: {pythonEngineUrl}/proposal/generate");
                var response = await client.PostAsJsonAsync($"{pythonEngineUrl}/proposal/generate", payload);

                if (response.IsSuccessStatusCode)
                {
                    var result = await response.Content.ReadFromJsonAsync<object>();
                    return Ok(result);
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError($"AI Engine returned {response.StatusCode}: {errorContent}");
                    return StatusCode((int)response.StatusCode, new { error = "AI Engine failed", details = errorContent });
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error generating proposal");
                return StatusCode(500, new { error = "An unexpected error occurred", details = ex.Message });
            }
        }
    }
}
