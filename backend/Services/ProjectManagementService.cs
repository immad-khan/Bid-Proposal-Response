using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using BackendNet.Models;

namespace BackendNet.Services
{
    public interface IProjectManagementService
    {
        Task<ProposalProjectDto> CreateProjectAsync(string name, string rfpBlobUrl);
        Task<IEnumerable<ProposalProjectDto>> GetProjectsAsync();
    }

    public class ProjectManagementService : IProjectManagementService
    {
        private readonly List<ProposalProjectDto> _projects = new();

        public async Task<ProposalProjectDto> CreateProjectAsync(string name, string rfpBlobUrl)
        {
            await Task.Delay(10);
            var project = new ProposalProjectDto
            {
                Id = Guid.NewGuid().ToString(),
                Name = name,
                RfpBlobUrl = rfpBlobUrl,
                CreatedAt = DateTime.UtcNow,
                Status = "Created"
            };
            _projects.Add(project);
            return project;
        }

        public async Task<IEnumerable<ProposalProjectDto>> GetProjectsAsync()
        {
            await Task.Delay(10);
            return _projects;
        }
    }
}
