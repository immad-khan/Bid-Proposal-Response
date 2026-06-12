using Microsoft.EntityFrameworkCore;
using BackendNet.Data;
using BackendNet.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace BackendNet.Services
{
    public interface IWorkspaceService
    {
        Task<Workspace> CreateWorkspaceAsync(string name, string description, string ownerId, string? workspaceId = null);
        Task<Workspace> GetWorkspaceAsync(string workspaceId);
        Task<ProposalVersion> SaveDraftAsync(string workspaceId, string content, string userId, string comment);
        Task<List<ProposalVersion>> GetVersionHistoryAsync(string workspaceId);
        Task<ProposalVersion> GetVersionAsync(string versionId);
        Task<string> ExportProposalAsync(string workspaceId, string format);
        Task<WorkspaceMember?> InviteMemberAsync(string workspaceId, string email, string role, string invitedBy);
    }

    public class WorkspaceService : IWorkspaceService
    {
        private readonly ApplicationDbContext _db;
        private readonly IBlobStorageService _blobStorage;
        private readonly IEmailService _emailService;
        private readonly IDocumentGenerator _documentGenerator;

        public WorkspaceService(
            ApplicationDbContext db, 
            IBlobStorageService blobStorage, 
            IEmailService emailService,
            IDocumentGenerator documentGenerator)
        {
            _db = db;
            _blobStorage = blobStorage;
            _emailService = emailService;
            _documentGenerator = documentGenerator;
        }

        public async Task<Workspace> CreateWorkspaceAsync(string name, string description, string ownerId, string? workspaceId = null)
        {
            var workspace = new Workspace
            {
                Id = !string.IsNullOrEmpty(workspaceId) ? workspaceId : Guid.NewGuid().ToString(),
                Name = name,
                Description = description,
                OwnerId = ownerId,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            _db.Workspaces.Add(workspace);
            
            // Add owner as Admin member
            _db.WorkspaceMembers.Add(new WorkspaceMember
            {
                WorkspaceId = workspace.Id,
                UserId = ownerId,
                Role = "Admin"
            });
            await _db.SaveChangesAsync();
            return workspace;
        }

        public async Task<Workspace> GetWorkspaceAsync(string workspaceId)
        {
            return await _db.Workspaces
                .Include(w => w.Members)
                .Include(w => w.Versions.OrderByDescending(v => v.VersionNumber))
                .FirstOrDefaultAsync(w => w.Id == workspaceId);
        }

        public async Task<ProposalVersion> SaveDraftAsync(string workspaceId, string content, string userId, string comment)
        {
            var workspace = await _db.Workspaces.FindAsync(workspaceId);
            if (workspace == null) throw new Exception("Workspace not found");

            var lastVersion = await _db.ProposalVersions
                .Where(v => v.WorkspaceId == workspaceId)
                .OrderByDescending(v => v.VersionNumber)
                .FirstOrDefaultAsync();
            int newVersionNumber = (lastVersion?.VersionNumber ?? 0) + 1;

            var version = new ProposalVersion
            {
                WorkspaceId = workspaceId,
                VersionNumber = newVersionNumber,
                Content = content,
                CreatedBy = userId,
                CreatedAt = DateTime.UtcNow,
                Comment = comment ?? string.Empty
            };
            _db.ProposalVersions.Add(version);
            workspace.UpdatedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync();
            return version;
        }

        public async Task<List<ProposalVersion>> GetVersionHistoryAsync(string workspaceId)
        {
            return await _db.ProposalVersions
                .Where(v => v.WorkspaceId == workspaceId)
                .OrderByDescending(v => v.VersionNumber)
                .ToListAsync();
        }

        public async Task<ProposalVersion> GetVersionAsync(string versionId)
        {
            var version = await _db.ProposalVersions.FindAsync(versionId);
            if (version == null)
            {
                throw new KeyNotFoundException($"Version {versionId} not found");
            }
            return version;
        }

        public async Task<string> ExportProposalAsync(string workspaceId, string format)
        {
            var latestVersion = await _db.ProposalVersions
                .Where(v => v.WorkspaceId == workspaceId)
                .OrderByDescending(v => v.VersionNumber)
                .FirstOrDefaultAsync();
            if (latestVersion == null) return string.Empty;

            // Convert HTML content to PDF or DOCX using helper service `IDocumentGenerator`
            var bytes = await _documentGenerator.GenerateAsync(latestVersion.Content, format);
            var fileName = $"proposal_{workspaceId}.{format.ToLower()}";
            var url = await _blobStorage.UploadGeneratedFileAsync(fileName, bytes);
            return url;
        }

        public async Task<WorkspaceMember?> InviteMemberAsync(string workspaceId, string email, string role, string invitedBy)
        {
            // Check if user exists in system by email, if not, create a pending invitation
            var user = await _db.Users.FirstOrDefaultAsync(u => u.Email == email);
            if (user == null)
            {
                // Create temporary invite record
                var invite = new PendingInvite
                {
                    WorkspaceId = workspaceId,
                    Email = email,
                    Role = role,
                    InvitedBy = invitedBy,
                    ExpiresAt = DateTime.UtcNow.AddDays(7)
                };
                _db.PendingInvites.Add(invite);
                await _db.SaveChangesAsync();

                // Send email with signup link that includes invite token
                await _emailService.SendInviteEmail(email, invite.Id);
                return null; // No member added yet
            }

            var member = new WorkspaceMember
            {
                WorkspaceId = workspaceId,
                UserId = user.Id,
                Role = role
            };
            _db.WorkspaceMembers.Add(member);
            await _db.SaveChangesAsync();
            return member;
        }
    }
}
