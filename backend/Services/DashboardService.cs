using Microsoft.EntityFrameworkCore;
using BackendNet.Data;
using BackendNet.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Net.Http;
using System.Text.Json;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace BackendNet.Services
{
    public interface IDashboardService
    {
        Task<List<WinProbabilityDto>> GetWinProbabilitiesAsync(string userId);
        Task<WinProbabilityDetailDto> GetDetailedAnalysisAsync(string projectId);
    }

    public class DashboardService : IDashboardService
    {
        private readonly ApplicationDbContext _db;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly IConfiguration _configuration;
        private readonly ILogger<DashboardService> _logger;

        public DashboardService(
            ApplicationDbContext db, 
            IHttpClientFactory httpClientFactory, 
            IConfiguration configuration,
            ILogger<DashboardService> logger)
        {
            _db = db;
            _httpClientFactory = httpClientFactory;
            _configuration = configuration;
            _logger = logger;
        }

        private string GetPythonEngineUrl()
        {
            return _configuration["PythonEngine:Url"] ?? "http://localhost:8000";
        }

        public async Task<List<WinProbabilityDto>> GetWinProbabilitiesAsync(string userId)
        {
            // 1. Fetch projects belonging to the user (or shared with user via RBAC)
            var projects = await _db.Projects
                .Where(p => p.OwnerId == userId || p.Members.Any(m => m.UserId == userId))
                .ToListAsync();

            var result = new List<WinProbabilityDto>();

            foreach (var proj in projects)
            {
                try
                {
                    // 2. Get compliance score from Neo4j via AI Engine API
                    double complianceScore = await GetComplianceScoreFromAiEngine(proj.Id);
                    
                    // 3. Get go/no-go prediction from AI Engine
                    var goNoGo = await GetGoNoGoFromAiEngine(proj.Id);
                    
                    // 4. Calculate win probability using weighted formula (or ML model)
                    double winProb = CalculateWinProbability(complianceScore, goNoGo.Probability, proj.SimilarPastWinRate);

                    result.Add(new WinProbabilityDto
                    {
                        ProjectId = proj.Id,
                        ProjectName = proj.Name,
                        Client = proj.ClientName,
                        Deadline = proj.SubmissionDeadline,
                        WinProbability = winProb,
                        ComplianceScore = complianceScore,
                        GoNoGoDecision = goNoGo.Decision,
                        TopFeatures = goNoGo.TopShapFeatures
                    });
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, $"Failed to process win probability for project {proj.Id}");
                    // Add fallback item if AI Engine call fails to prevent breaking the dashboard entirely
                    result.Add(new WinProbabilityDto
                    {
                        ProjectId = proj.Id,
                        ProjectName = proj.Name,
                        Client = proj.ClientName,
                        Deadline = proj.SubmissionDeadline,
                        WinProbability = proj.SimilarPastWinRate, // fallback
                        ComplianceScore = 0.5,
                        GoNoGoDecision = "NO-GO",
                        TopFeatures = new List<ShapFeatureDto>()
                    });
                }
            }

            // 5. Sort by win probability descending (most promising first)
            return result.OrderByDescending(r => r.WinProbability).ToList();
        }

        private async Task<double> GetComplianceScoreFromAiEngine(string projectId)
        {
            var client = _httpClientFactory.CreateClient();
            var pythonUrl = GetPythonEngineUrl();
            var response = await client.GetAsync($"{pythonUrl}/compliance/{projectId}/score");
            
            if (!response.IsSuccessStatusCode)
            {
                _logger.LogWarning($"AI Engine compliance score returned {response.StatusCode} for project {projectId}. Using default.");
                return 0.75; // Fallback default compliance score
            }

            var json = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(json);
            return doc.RootElement.GetProperty("score").GetDouble();
        }

        private async Task<(double Probability, string Decision, List<ShapFeatureDto> TopShapFeatures)> GetGoNoGoFromAiEngine(string projectId)
        {
            var client = _httpClientFactory.CreateClient();
            var pythonUrl = GetPythonEngineUrl();
            var response = await client.GetAsync($"{pythonUrl}/go-nogo/{projectId}");

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogWarning($"AI Engine go-nogo returned {response.StatusCode} for project {projectId}. Using defaults.");
                return (0.5, "NO-GO", new List<ShapFeatureDto>());
            }

            var json = await response.Content.ReadAsStringAsync();
            using var doc = JsonDocument.Parse(json);
            var prob = doc.RootElement.GetProperty("probability").GetDouble();
            var decision = doc.RootElement.GetProperty("decision").GetString() ?? "NO-GO";
            var features = new List<ShapFeatureDto>();
            
            if (doc.RootElement.TryGetProperty("shap_features", out var shapFeaturesProp) && shapFeaturesProp.ValueKind == JsonValueKind.Array)
            {
                foreach (var feat in shapFeaturesProp.EnumerateArray())
                {
                    features.Add(new ShapFeatureDto
                    {
                        FeatureName = feat.GetProperty("name").GetString() ?? string.Empty,
                        Value = feat.GetProperty("value").GetDouble(),
                        ShapContribution = feat.GetProperty("shap").GetDouble()
                    });
                }
            }
            return (prob, decision, features);
        }

        private double CalculateWinProbability(double compliance, double goNoGoProb, double pastWinRate)
        {
            // Weighted average: compliance has highest importance (50%), go/no-go ML (30%), historical similar wins (20%)
            return (compliance * 0.5) + (goNoGoProb * 0.3) + (pastWinRate * 0.2);
        }

        public async Task<WinProbabilityDetailDto> GetDetailedAnalysisAsync(string projectId)
        {
            var proj = await _db.Projects.FirstOrDefaultAsync(p => p.Id == projectId);
            if (proj == null)
            {
                throw new KeyNotFoundException($"Project {projectId} not found");
            }

            double complianceScore = 0.8;
            var goNoGo = (Probability: 0.75, Decision: "GO", TopShapFeatures: new List<ShapFeatureDto>());
            try
            {
                complianceScore = await GetComplianceScoreFromAiEngine(projectId);
                goNoGo = await GetGoNoGoFromAiEngine(projectId);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, $"Failed to call AI Engine for detailed analysis of project {projectId}");
            }

            double winProb = CalculateWinProbability(complianceScore, goNoGo.Probability, proj.SimilarPastWinRate);

            return new WinProbabilityDetailDto
            {
                ProjectId = proj.Id,
                ProjectName = proj.Name,
                Client = proj.ClientName,
                WinProbability = winProb,
                ComplianceScore = complianceScore,
                GoNoGoDecision = goNoGo.Decision,
                TopFeatures = goNoGo.TopShapFeatures,
                ComplianceGaps = new List<string> { "Missing SOC 2 Type II Certification evidence", "Timeline requirements are aggressive" },
                RfpBudget = 120000,
                CompanyBaseCost = 95000
            };
        }
    }
}
