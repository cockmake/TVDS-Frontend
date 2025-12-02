// const SERVER_HOST = "http://127.0.0.1:8080";
const SERVER_HOST = "http://192.168.188.2:8081";
// const SERVER_HOST = "http://192.168.188.6:8082";
import {reactive} from "vue";

// const SERVER_HOST = "http://10.0.100.210:8082";
// const SERVER_HOST = "http://10.143.8.138:8082";
const SERVER_API_VERSION = "/api/v1";
const SERVER_API_URL = SERVER_HOST + SERVER_API_VERSION;

const DIRECTION_NAME = [
    "右侧", "左侧", "底中", "底右", "底左"
]

const VehicleSearchKey = reactive({
    dateRange: null,
    vehicleInfoList: [],
    currentPage: 1,
    pageSize: 50,
})
export {SERVER_HOST, SERVER_API_VERSION, SERVER_API_URL, DIRECTION_NAME, VehicleSearchKey};