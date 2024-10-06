using JsonApi.Entities;
using Microsoft.AspNetCore.Mvc;

namespace JsonApi.Controllers
{
    [ApiController]
    [Route("[controller]")]
    public class JsonController : ControllerBase
    {
        [HttpPost("GetUserData")]
        public async Task<UserDataViewModel> GetUserData(string email, string phrase)
        {
            var entityService = new EntityService();
            var user = (await entityService
                .FindByProps((User user) => user.Id == email && user.Phrase == phrase))
                .FirstOrDefault();
                
            if (user != null)
            {
                var ulinks = await entityService.FindByProps((UserLink userLink) => userLink.Source == user.Id);
                var nodeIds = ulinks.SelectMany(x => x.Nodes).Distinct();
                
                var groupNodes = (await entityService.FindByProps((GroupLink x) => ulinks.SelectMany(x => x.Groups).Distinct().Contains(x.Source)))
                    .SelectMany(x=>x.Nodes);

                var nodes = await entityService.FindByProps((Node node) =>  nodeIds.Concat(groupNodes).Contains(node.Id));
            }

            return new UserDataViewModel();
        }
    }

    public class UserDataViewModel
    {
        public Node[] Nodes { get; set; } = { };
        public Group[] Groups { get; set; } = { };
        public GroupLink[] GroupLinks { get; private set; } = { };
        public NodeLink[] NodeLinks {  get; private set; } = { }; 
    }
}