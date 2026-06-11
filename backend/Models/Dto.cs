using System;

namespace BackendNet.Models
{
    public class ProposalProjectDto
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string RfpBlobUrl { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public string Status { get; set; } = string.Empty;
    }

    public class RfpUploadResponseDto
    {
        public string Status { get; set; } = string.Empty;
        public string JobId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string BlobUrl { get; set; } = string.Empty;
    }
}
