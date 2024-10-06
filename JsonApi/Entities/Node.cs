using System.Text.Json.Serialization;
using System.Text.Json;
using System.Reflection.Emit;

namespace JsonApi.Entities
{
    public enum NodeLinkType
    {
        Natural,
        Lawed
    }

    public class BaseEntity
    {
        public required string Id { get; set; }
        [JsonExtensionData]
        public Dictionary<string, JsonElement>? Expando { get; set; }
        public required string Label { get; set; }
    }

    public class Node : BaseEntity
    {
        public required  string Name { get; set; }
        public string[] AltName { get; set; } = { };
        public string[] AltIds { get; set; } = { };
    }

    public class Group : BaseEntity
    {
        public required  string Name { get; set; }
        public required  string Description { get; set; }
        public string[] Locations { get; set; } = { };
    }

    public class Location : BaseEntity
    {
        public required string Name { get; set; }
    }

    public class User : BaseEntity
    {
        public required string Name { get; set; }
        public required string Phrase { get; set; }
    }

    public class NodeLink : BaseEntity
    {
        public required string Source { get; set; }
        public required string Target { get; set; }
        public NodeLinkType NodeLinkType { get; set; }

        public string? LinkedOn { get; set; }
        public string? BrokeOn { get; set; }
    }

    public class GroupLink : BaseEntity
    {
        public required string Source { get; set; }
        public string[] Nodes { get; set; } = { };

        public string[] Groups { get; set; } = { };
    }

    public class LocationLink : BaseEntity
    {
        public required string Source { get; set; }
        public string[] Groups { get; set; } = { };
    }

    public class UserLink : BaseEntity
    {
        public required string Source { get; set; }
        public string[] Nodes { get; set; } = { };
        public string[] Groups { get; set; } = { };
    }
}