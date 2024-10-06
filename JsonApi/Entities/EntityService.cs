using System.Reflection;
using System.Text.Json;

namespace JsonApi.Entities
{
    public class EntityService
    {
        private static List<BaseEntity> entityStore = new List<BaseEntity>();
        private static string dataFile = "data.json";

        public void LoadFile()
        {
            if (!File.Exists(dataFile))
                using (var f = File.CreateText(dataFile)) f.Write(JsonSerializer.Serialize(entityStore));
            if (File.Exists(dataFile) && !entityStore.Any())
            {
                this.ParseDataAndLoad();
            }
        }

        public void LoadAs<TEntity>(dynamic x) where TEntity : BaseEntity
        {
            var ns = JsonSerializer.Serialize(x);
            var n = JsonSerializer.Deserialize<TEntity>(ns);
            entityStore.Add(n);
        }

        private void ParseDataAndLoad()
        {
            var jsonString = File.ReadAllText(dataFile);
            var arr = JsonSerializer.Deserialize<List<dynamic>>(jsonString);

            arr.ForEach(x =>
            {
                try
                {
                    var label = x.GetProperty("Label").GetString();
                    var type = Type.GetType($"JsonApi.Entities.{label}");
                    if (type != null)
                    {
                        MethodInfo method = typeof(EntityService).GetMethod("LoadAs")!;
                        MethodInfo genericMethod = method.MakeGenericMethod(type);
                        genericMethod.Invoke(this, new object[] { x as dynamic });
                    }
                }
                catch (Exception ex)
                {
                }
            });
        }

        public void Save()
        {
            File.WriteAllText(dataFile, JsonSerializer.Serialize(entityStore));
        }

        public List<BaseEntity> GetEntitiesById(string id)
        {
            return entityStore.FindAll(x => x.Id == id);
        }

        public async Task<IEnumerable<TEntity>> FindByProps<TEntity>(Predicate<TEntity> match)
            where TEntity : BaseEntity
        {
            Predicate<BaseEntity> pred = x =>
                x.Label == typeof(TEntity).Name
                && x is TEntity entity
                && match(entity);

            if (pred != null)
                return entityStore.FindAll(pred).Cast<TEntity>();
            return [];
        }

        public async Task<TEntity?> FindOneByProps<TEntity>(Predicate<TEntity> match)
            where TEntity : BaseEntity
        {
            var result = FindByProps(match);
            if (result != null) return (await result).FirstOrDefault();
            return null;
        }

        public void AddEntity(params BaseEntity[] entities)
        {
            entityStore.AddRange(entities);
            Task.Run(() => this.Save());
        }

        //public void UpdateEntity(params BaseEntity[] entities)
        //{
        //    //entities.ToList().ForEach(e => entityStore.FirstOrDefault(y => e.Id == y.Id);
        //    Task.Run(() => this.Save());
        //}
    }
}