package nab.detectors.htmjava;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.joda.time.DateTimeZone;
import org.numenta.nupic.Connections;
import org.numenta.nupic.Parameters;
import org.numenta.nupic.Parameters.KEY;
import org.numenta.nupic.algorithms.Anomaly;
import org.numenta.nupic.algorithms.SpatialPooler;
import org.numenta.nupic.algorithms.TemporalMemory;
import org.numenta.nupic.network.Layer;
import org.numenta.nupic.network.Network;
import org.numenta.nupic.network.Region;
import org.numenta.nupic.network.sensor.ObservableSensor;
import org.numenta.nupic.network.sensor.Publisher;
import org.numenta.nupic.network.sensor.Sensor;
import org.numenta.nupic.network.sensor.SensorParams;
import org.numenta.nupic.util.Tuple;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

public class HTMModel {
    protected static final Logger LOGGER = LoggerFactory.getLogger(HTMModel.class);

    private Network network;

    private Publisher publisher;

    /**
     * Create HTM Model to be used by NAB
     * @param modelParams OPF Model parameters to parameters from
     */
    public HTMModel(JsonNode modelParams) {
        if(LOGGER.isDebugEnabled()) {
            LOGGER.debug("OPF Model Params:" + modelParams.toString());
        }

        // Create Sensor publisher to push NAB input data to network
        publisher = Publisher.builder()
                .addHeader("timestamp,value")
                .addHeader("datetime,float")
                .addHeader("T,B")
                .build();

        // Get updated model parameters
        Parameters parameters = getModelParameters(modelParams);
        if(LOGGER.isDebugEnabled()) {
            LOGGER.debug("HTM java Parameters:" + parameters.toString());
        }

        // Create NAB Network
        network = Network.create("NAB Network", parameters)
                .add(Network.createRegion("NAB Region")
                    .add(Network.createLayer("NAB Layer", parameters)
                        .add(Anomaly.create())
                        .add(new TemporalMemory())
                        .add(new SpatialPooler())
                        .add(Sensor.create(ObservableSensor::create,
                                SensorParams.create(SensorParams.Keys::obs, "Manual Input", publisher)))));

    }

    /**
     * Update encoders parameters
     * @param modelParams OPF Model parameters to get encoder parameters from
     * @return Updated Encoder parameters suitable for {@link Parameters.KEY.FIELD_ENCODING_MAP}
     */
    public Map<String, Map<String, Object>> getFieldEncodingMap(JsonNode modelParams) {

        Map<String, Map<String, Object>> fieldEncodings = new HashMap<>();
        String fieldName;
        Map<String, Object> fieldMap;
        JsonNode encoders = modelParams.path("encoders");
        for (JsonNode node : encoders) {
            if (node.isNull())
                continue;

            fieldName = node.path("fieldname").textValue();
            fieldMap = fieldEncodings.get(fieldName);
            if (fieldMap == null) {
                fieldMap = new HashMap<>();
                fieldMap.put("fieldName", fieldName);
                fieldEncodings.put(fieldName, fieldMap);
            }
            fieldMap.put("encoderType", node.path("type").textValue());
            if (node.has("timeOfDay")) {
                JsonNode timeOfDay = node.get("timeOfDay");
                fieldMap.put("fieldType", "datetime");
                fieldMap.put(KEY.DATEFIELD_PATTERN.getFieldName(), "YYYY-MM-dd HH:mm:ss");
                fieldMap.put(KEY.DATEFIELD_TOFD.getFieldName(),
                        new Tuple(timeOfDay.get(0).asInt(), timeOfDay.get(1).asDouble()));
            } else {
                fieldMap.put("fieldType", "float");
            }
            if (node.has("resolution")) {
                fieldMap.put("resolution", node.get("resolution").asDouble());
            }
        }
        return fieldEncodings;
    }

    /**
     * Update Spatial Pooler parameters
     * @param modelParams OPF Model parameters to get spatial pooler parameters from
     * @return Updated Spatial Pooler parameters
     */
    public Parameters getSpatialPoolerParams(JsonNode modelParams) {
        Parameters p = Parameters.getSpatialDefaultParameters();
        JsonNode spParams = modelParams.path("spParams");
        p.setParameterByKey(KEY.SP_VERBOSITY, spParams.get("spVerbosity").asInt());
        p.setParameterByKey(KEY.MAX_BOOST, spParams.get("maxBoost").asDouble());
        p.setParameterByKey(KEY.SYN_PERM_INACTIVE_DEC, spParams.get("synPermInactiveDec").asDouble());
        p.setParameterByKey(KEY.SYN_PERM_CONNECTED, spParams.get("synPermConnected").asDouble());
        p.setParameterByKey(KEY.SYN_PERM_ACTIVE_INC, spParams.get("synPermActiveInc").asDouble());
        p.setParameterByKey(KEY.SEED, spParams.get("seed").asInt());
        p.setParameterByKey(KEY.NUM_ACTIVE_COLUMNS_PER_INH_AREA, spParams.get("numActiveColumnsPerInhArea").asDouble());
        p.setParameterByKey(KEY.GLOBAL_INHIBITION, spParams.get("globalInhibition").asBoolean());
        p.setParameterByKey(KEY.POTENTIAL_PCT, spParams.get("potentialPct").asDouble());

        return p;
    }

    /**
     * Update Temporal Memory parameters
     * @param modelParams OPF Model parameters to get Temporal Memory parameters from
     * @return Updated Temporal Memory parameters
     */
    public Parameters getTemporalMemoryParams(JsonNode modelParams) {
        Parameters p = Parameters.getTemporalDefaultParameters();
        JsonNode tpParams = modelParams.path("tpParams");
        p.setParameterByKey(KEY.COLUMN_DIMENSIONS, new int[]{tpParams.get("columnCount").asInt()});
        p.setParameterByKey(KEY.INPUT_DIMENSIONS, new int[]{tpParams.get("inputWidth").asInt()});
        p.setParameterByKey(KEY.ACTIVATION_THRESHOLD, tpParams.get("activationThreshold").asInt());
        p.setParameterByKey(KEY.CELLS_PER_COLUMN, tpParams.get("cellsPerColumn").asInt());
        p.setParameterByKey(KEY.PERMANENCE_INCREMENT, tpParams.get("permanenceInc").asDouble());
        p.setParameterByKey(KEY.MIN_THRESHOLD, tpParams.get("minThreshold").asInt());
        p.setParameterByKey(KEY.TM_VERBOSITY, tpParams.get("verbosity").asInt());
        // +        "globalDecay": 0.0,
        p.setParameterByKey(KEY.INITIAL_PERMANENCE, tpParams.get("initialPerm").asDouble());
        // +        "maxAge": 0,
        // +        "maxSegmentsPerCell": 128,
        // +        "maxSynapsesPerSegment": 128,
        p.setParameterByKey(KEY.PERMANENCE_DECREMENT, tpParams.get("permanenceDec").asDouble());
        p.setParameterByKey(KEY.PREDICTED_SEGMENT_DECREMENT, tpParams.get("predictedSegmentDecrement").asDouble());
        p.setParameterByKey(KEY.SEED, tpParams.get("seed").asInt());
        p.setParameterByKey(KEY.MAX_NEW_SYNAPSE_COUNT, tpParams.get("newSynapseCount").intValue());

        return p;
    }

    /**
     * Update Sensor parameters
     * @param modelParams OPF Model parameters to get Sensor parameters from
     * @return Updated Sensor parameters
     */
    public Parameters getSensorParams(JsonNode modelParams) {
        JsonNode sensorParams = modelParams.path("sensorParams");
        Map<String, Map<String, Object>> fieldEncodings = getFieldEncodingMap(sensorParams);
        Parameters p = Parameters.empty();
        p.setParameterByKey(KEY.CLIP_INPUT, true);
        p.setParameterByKey(KEY.FIELD_ENCODING_MAP, fieldEncodings);
        return p;
    }

    /**
     * Update NAB parameters
     * @param params OPF parameters to get NAB model parameters from
     * @return Updated Model parameters
     */
    public Parameters getModelParameters(JsonNode params) {
        JsonNode modelParams = params.path("modelParams");
        return Parameters.getAllDefaultParameters()
                .union(getSpatialPoolerParams(modelParams))
                .union(getTemporalMemoryParams(modelParams))
                .union(getSensorParams(modelParams));
    }

    public Publisher getPublisher() {
        return publisher;
    }

    public Network getNetwork() {
        return network;
    }


    public void showDebugInfo() {
        Region region = network.getHead();
        Layer<?> layer = region.lookup("NAB Layer");
        Connections connections = layer.getConnections();
        double[] cycles = connections.getActiveDutyCycles();
        int spActive = 0;
        for (int i = 0; i < cycles.length; i++) {
            if (cycles[i] > 0) {
                spActive++;
            }
        }
        LOGGER.debug("SP ActiveDutyCycles: " + spActive);

    }

    /**
     * Launch htm.java NAB detector
     *
     * Usage:
     *      As a standalone application (for debug purpose only):
     *
     *          java -jar htm.java-nab.jar "{\"modelParams\":{....}}" < nab_data.csv > anomalies.out
     *
     *      As a NAB detector (see 'htmjava_detector.py'):
     *
     *          python run.py --detect --score --normalize -d htmjava
     *
     */
    public static void main(String[] args) {
        try {
            if (args.length != 1) {
                throw new IllegalArgumentException("Expecting JSON with OPF parameters as the only command line argument");
            }
            String modelParams = args[0];
            if(LOGGER.isDebugEnabled()) {
                LOGGER.debug("Command line argument:" + modelParams);
            }

            // Force timezone to UTC
            DateTimeZone.setDefault(DateTimeZone.UTC);

            // Parse OPF Model Parameters
            ObjectMapper mapper = new ObjectMapper();
            JsonNode params = mapper.readTree(modelParams);

            // Create NAB Network Model
            HTMModel model = new HTMModel(params);
            Network network = model.getNetwork();

            // Output raw anomaly score
            network.observe().subscribe((inference) -> {
                System.out.println(inference.getAnomalyScore());
            });
            network.start();

            // Pipe stdin to network
            Publisher publisher = model.getPublisher();
            BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
            String line;
            while ((line = in.readLine()) != null && line.trim().length() > 0) {
                publisher.onNext(line);
            }

            if(LOGGER.isDebugEnabled()) {
                model.showDebugInfo();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
