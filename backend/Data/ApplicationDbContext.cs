using Microsoft.EntityFrameworkCore;
using BackendNet.Models;

namespace BackendNet.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<User> Users { get; set; } = null!;
        public DbSet<Project> Projects { get; set; } = null!;
        public DbSet<ProjectMember> ProjectMembers { get; set; } = null!;
        public DbSet<Workspace> Workspaces { get; set; } = null!;
        public DbSet<WorkspaceMember> WorkspaceMembers { get; set; } = null!;
        public DbSet<ProposalVersion> ProposalVersions { get; set; } = null!;
        public DbSet<PendingInvite> PendingInvites { get; set; } = null!;

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // Configure relationships if necessary
            modelBuilder.Entity<WorkspaceMember>()
                .HasOne(m => m.Workspace)
                .WithMany(w => w.Members)
                .HasForeignKey(m => m.WorkspaceId);

            modelBuilder.Entity<ProposalVersion>()
                .HasOne(v => v.Workspace)
                .WithMany(w => w.Versions)
                .HasForeignKey(v => v.WorkspaceId);

            modelBuilder.Entity<ProjectMember>()
                .HasOne(pm => pm.Project)
                .WithMany(p => p.Members)
                .HasForeignKey(pm => pm.ProjectId);
        }
    }
}
