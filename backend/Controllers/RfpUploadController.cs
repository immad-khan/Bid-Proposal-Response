using Microsoft.AspNetCore.Mvc;
using Azure.Storage.Blobs;
using System.Text.Json;

namespace BackendNet.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class RfpUploadController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;
        private readonly ILogger<RfpUploadController> _logger;

        public RfpUploadController(
            IHttpClientFactory httpClientFactory, 
            IConfiguration configuration,
            ILogger<RfpUploadController> logger)
        {
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

                // 1. Upload to Azure Blob Storage
                var connectionString = _configuration["AzureStorage:ConnectionString"];
                
                if (string.IsNullOrEmpty(connectionString))
                {
                    _logger.LogError("Azure Storage connection string not configured");
                    return StatusCode(500, new { error = "Storage not configured" });
                }

                var blobServiceClient = new BlobServiceClient(connectionString);
                var containerClient = blobServiceClient.GetBlobContainerClient("rfp-uploads");
                await containerClient.CreateIfNotExistsAsync();

                var uniqueFileName = $"{Guid.NewGuid()}_{file.FileName}";
                var blobClient = containerClient.GetBlobClient(uniqueFileName);
                
                using (var stream = file.OpenReadStream())
                {
                    await blobClient.UploadAsync(stream, overwrite: true);
                }

                var blobUrl = blobClient.Uri.ToString();
                _logger.LogInformation($"File uploaded to blob: {blobUrl}");

                // 2. Trigger the Python Engine
                var jobId = Guid.NewGuid().ToString();
                var payload = new { jobId, blobUrl, filename = file.FileName };

                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromMinutes(5); // Adjust as needed
                
                var pythonEngineUrl = _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
                var response = await client.PostAsJsonAsync($"{pythonEngineUrl}/process-rfp", payload);

                if (response.IsSuccessStatusCode)
                {
                    _logger.LogInformation($"Job {jobId} submitted to AI engine successfully");
                    return Ok(new 
                    { 
                        status = "Success", 
                        jobId, 
                        message = "Engine triggered.",
                        blobUrl 
                    });
                }
                else
                {
                    var errorContent = await response.Content.ReadAsStringAsync();
                    _logger.LogError($"AI Engine returned {response.StatusCode}: {errorContent}");
                    return StatusCode(500, new 
                    { 
                        error = "Failed to reach AI Engine.",
                        details = errorContent 
                    });
                }
            }
            catch (Azure.RequestFailedException ex)
            {
                _logger.LogError(ex, "Azure Storage error");
                return StatusCode(500, new { error = "Storage upload failed", details = ex.Message });
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError(ex, "Python Engine connection failed");
                return StatusCode(500, new { error = "Cannot connect to AI Engine. Is it running on port 8000?", details = ex.Message });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error during upload");
                return StatusCode(500, new { error = "An unexpected error occurred", details = ex.Message });
            }
        }
    }
}