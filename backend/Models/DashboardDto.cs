using System;
using System.Collections.Generic;

namespace BackendNet.Models
{
    public class WinProbabilityDto
    {
        public string ProjectId { get; set; } = string.Empty;
        public string ProjectName { get; set; } = string.Empty;
        public string Client { get; set; } = string.Empty;
        public DateTime Deadline { get; set; }
        public double WinProbability { get; set; }  // 0.0 to 1.0
        public double ComplianceScore { get; set; } // 0.0 to 1.0
        public string GoNoGoDecision { get; set; } = string.Empty;  // "Go" or "No-Go"
        public List<ShapFeatureDto> TopFeatures { get; set; } = new();
    }

    public class ShapFeatureDto
    {
        public string FeatureName { get; set; } = string.Empty;
        public double Value { get; set; }
        public double ShapContribution { get; set; }
    }

    public class WinProbabilityDetailDto
    {
        public string ProjectId { get; set; } = string.Empty;
        public string ProjectName { get; set; } = string.Empty;
        public string Client { get; set; } = string.Empty;
        public double WinProbability { get; set; }
        public double ComplianceScore { get; set; }
        public string GoNoGoDecision { get; set; } = string.Empty;
        public List<ShapFeatureDto> TopFeatures { get; set; } = new();
        public List<string> ComplianceGaps { get; set; } = new();
        public double RfpBudget { get; set; }
        public double CompanyBaseCost { get; set; }
    }
}
