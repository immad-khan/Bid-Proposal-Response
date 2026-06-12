using System;
using System.Collections.Generic;
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
    public class ComplianceController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;
        private readonly ILogger<ComplianceController> _logger;

        public ComplianceController(
            IHttpClientFactory httpClientFactory,
            IConfiguration configuration,
            ILogger<ComplianceController> logger)
        {
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
            _logger = logger;
        }

        [HttpGet("matrix")]
        public async Task<IActionResult> GetMatrix()
        {
            try
            {
                var pythonEngineUrl = _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
                var client = _httpClientFactory.CreateClient();
                
                var response = await client.GetAsync($"{pythonEngineUrl}/compliance/matrix");

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
                _logger.LogError(ex, "Error getting matrix");
                return StatusCode(500, new { error = "An unexpected error occurred", details = ex.Message });
            }
        }

        [HttpPost("go-nogo")]
        public async Task<IActionResult> EvaluateGoNoGo([FromBody] Dictionary<string, float> features)
        {
            try
            {
                var pythonEngineUrl = _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
                var client = _httpClientFactory.CreateClient();
                
                var response = await client.PostAsJsonAsync($"{pythonEngineUrl}/compliance/evaluate-bid", features);

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
                _logger.LogError(ex, "Error evaluating go-nogo");
                return StatusCode(500, new { error = "An unexpected error occurred", details = ex.Message });
            }
        }
    }
}
