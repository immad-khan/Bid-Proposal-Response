using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace BackendNet.Models
{
    public class User
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Username { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
    }

    public class Project
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string ClientName { get; set; } = string.Empty;
        public DateTime SubmissionDeadline { get; set; }
        public double SimilarPastWinRate { get; set; }
        public string OwnerId { get; set; } = string.Empty;
        public ICollection<ProjectMember> Members { get; set; } = new List<ProjectMember>();
    }

    public class ProjectMember
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string ProjectId { get; set; } = string.Empty;
        public Project Project { get; set; } = null!;
        public string UserId { get; set; } = string.Empty;
    }

    public class Workspace
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public string OwnerId { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public DateTime UpdatedAt { get; set; }
        public ICollection<WorkspaceMember> Members { get; set; } = new List<WorkspaceMember>();
        public ICollection<ProposalVersion> Versions { get; set; } = new List<ProposalVersion>();
    }

    public class WorkspaceMember
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string WorkspaceId { get; set; } = string.Empty;
        public Workspace Workspace { get; set; } = null!;
        public string UserId { get; set; } = string.Empty;
        public string Role { get; set; } = string.Empty; // "Admin", "Editor", "Viewer", "ComplianceOfficer"
    }

    public class ProposalVersion
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string WorkspaceId { get; set; } = string.Empty;
        public Workspace Workspace { get; set; } = null!;
        public int VersionNumber { get; set; }
        public string Content { get; set; } = string.Empty; // JSON or HTML from editor
        public string CreatedBy { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; }
        public string Comment { get; set; } = string.Empty;
    }

    public class PendingInvite
    {
        [Key]
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string WorkspaceId { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string Role { get; set; } = string.Empty;
        public string InvitedBy { get; set; } = string.Empty;
        public DateTime ExpiresAt { get; set; }
    }
}
