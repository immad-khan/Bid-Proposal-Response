using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading.Tasks;
using BackendNet.Models;

namespace BackendNet.Services
{
    public interface IProjectManagementService
    {
        Task<ProposalProjectDto> CreateProjectAsync(string name, string rfpBlobUrl);
        Task<IEnumerable<ProposalProjectDto>> GetProjectsAsync();
        Task<ProposalProjectDto?> GetProjectByIdAsync(string id);
        Task<bool> UpdateProjectStatusAsync(string id, string status);
    }

    public class ProjectManagementService : IProjectManagementService
    {
        private static readonly ConcurrentDictionary<string, ProposalProjectDto> _projects = new();

        public async Task<ProposalProjectDto> CreateProjectAsync(string name, string rfpBlobUrl)
        {
            await Task.Delay(5); // Simulate async operation
            var project = new ProposalProjectDto
            {
                Id = Guid.NewGuid().ToString(),
                Name = name,
                RfpBlobUrl = rfpBlobUrl,
                CreatedAt = DateTime.UtcNow,
                Status = "Created"
            };

            _projects.TryAdd(project.Id, project);
            return project;
        }

        public async Task<IEnumerable<ProposalProjectDto>> GetProjectsAsync()
        {
            await Task.Delay(5);
            return _projects.Values;
        }

        public async Task<ProposalProjectDto?> GetProjectByIdAsync(string id)
        {
            await Task.Delay(5);
            _projects.TryGetValue(id, out var project);
            return project;
        }

        public async Task<bool> UpdateProjectStatusAsync(string id, string status)
        {
            await Task.Delay(5);
            if (_projects.TryGetValue(id, out var project))
            {
                project.Status = status;
                return true;
            }
            return false;
        }
    }
}
