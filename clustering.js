var fs = require('fs');
var pgp = require('pg-promise')();
var db;

// predefined clustering radius for each zoom level (in meters)
var zoom_level_radius =
{
    16: 100,
    15: 200,
    14: 500,
    13: 1000,
    12: 2000,
    11: 3000,
    10: 4000,
    9: 7000,
    8: 15000,
    7: 25000,
    6: 50000,
    5: 100000,
    4: 200000,
    3: 400000,
    2: 700000
};

process.on('config', (config, callback) => {
    console.log('clusterapp: Configuration: ', config);
    // connecting to PostgreSQL instance
    // example: postgres://dbname:dbpassword@localhost:5432/places
    db = pgp(config['connection_string']);
    callback();
    start_clustering();
});

String.prototype.format = function()
{
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
var regexp = new RegExp('\\{'+i+'\\}', 'gi');
formatted = formatted.replace(regexp, arguments[i]);
}
return formatted;
};
// create cluster table for each zoom level
function create_cluster_zooom_tables() {
db.task(t => {
        return t.batch([
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [2]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [3]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [4]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [5]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [6]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [7]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [8]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [9]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [10]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [11]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [12]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [13]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                    " centroid GEOMETRY, classify INTEGER);", [14]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                      " centroid GEOMETRY, classify INTEGER);", [15]),
                t.none("CREATE TABLE IF NOT EXISTS clusters_zoom_$1(cluster SERIAL PRIMARY KEY, pt_count INTEGER," +
                       " centroid GEOMETRY, classify INTEGER);", [16])
        ]);
    }).then(data => {
        console.log("create_cluster_zooom_tables: cluster tables created: " + data);
    }).catch(error => {
        console.log("create_cluster_zooom_tables:ERROR: " + error);
        finish_clustering({'ERROR': 'Creating tables failed: ' + error});
    });
}

// create make_cluster function for each zoom level
function create_cluster_functions()
{
    var cluster_func_query =
        "CREATE OR REPLACE FUNCTION make_cluster{0}() RETURNS INTEGER AS\n" +
        "$$\n" +
        "DECLARE start_place GEOGRAPHY;\n" +
        "DECLARE cluster_id INTEGER;\n" +
        "DECLARE ids INTEGER[];\n" +
         "BEGIN\n" +
            "SELECT place INTO start_place FROM places WHERE cluster{0} IS NULL limit 1;\n" +
            "IF start_place is NULL THEN\n" +
                "RETURN -1;\n" +
            "END IF;\n" +
            "SELECT array_agg(id) INTO ids FROM places WHERE cluster{0} is NULL AND ST_DWithin(start_place, place, {1});" +
            "INSERT INTO clusters_zoom_{0}(pt_count, centroid)\n" +
            "SELECT count(place), ST_Centroid(ST_Union(place::geometry)) FROM places, unnest(ids) as pid\n" +
            "WHERE id = pid\n" +
            "RETURNING cluster INTO cluster_id;\n" +
            "UPDATE places SET cluster{0} = cluster_id FROM unnest(ids) as pid WHERE id = pid;\n" +
            "RETURN cluster_id;\n" +
        "END;\n" +
        "$$  LANGUAGE plpgsql";

    for (var zoom_level in zoom_level_radius)
    {
        var query_create_func = cluster_func_query.format(zoom_level, zoom_level_radius[zoom_level]);
        db.none(query_create_func)
          .then(result => {
              console.log("create_cluster_functions: function created successfully");
          })
          .catch(error => {
              console.log('create_cluster_functions: Creating clustring function failed due: ' + error);
              finish_clustering({'ERROR': 'Creating functions failed: ' + error});
          });
    }
}

// creating cluster for each zoom level
function make_clusters()
{
    var query =
            "DO\n" +
            "$do$\n" +
            "DECLARE cluster_id INTEGER;\n" +
            "BEGIN\n" +
                "SELECT 0 INTO cluster_id;\n" +
                "WHILE cluster_id != -1\n" +
                "LOOP\n" +
                "SELECT make_cluster$1() INTO cluster_id;\n" +
                "END LOOP;\n" +
            "END\n" +
            "$do$;";

    db.task(t => {
        return t.batch([
                t.none(query, [2]),
                t.none(query, [3]),
                t.none(query, [4]),
                t.none(query, [5]),
                t.none(query, [6]),
                t.none(query, [7]),
                t.none(query, [8]),
                t.none(query, [9]),
                t.none(query, [10]),
                t.none(query, [11]),
                t.none(query, [12]),
                t.none(query, [13]),
                t.none(query, [14]),
                t.none(query, [15]),
                t.none(query, [16])
        ]);
    }).then(data => {
        console.log("make_clusters: cluster created: " + data);
        finish_clustering({'OK': ''});
    }).catch(error => {
        console.log("make_clusters:ERROR: " + error);
        finish_clustering({'ERROR': 'Creating clusters failed: ' + error});
    });
}

function start_clustering()
{
    create_cluster_zooom_tables();
    create_cluster_functions();
    make_clusters();
}

function finish_clustering(status)
{
    pgp.end();
    process.send({'status': status});
}
