import { rpcCall } from './xmpp';

export class IAbortable {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
}

export class IAcquisition {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
  public async acquire_target(): Promise<{string: any}> {
    return await rpcCall(this.jid, 'acquire_target');
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
}

export class IAutoFocus {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
  public async auto_focus(count: number, step: number, exposure_time: number): Promise<[number, number]> {
    return await rpcCall(this.jid, 'auto_focus', [count, step, exposure_time]);
  }
  public async auto_focus_status(): Promise<{string: any}> {
    return await rpcCall(this.jid, 'auto_focus_status');
  }
}

export class IAutoGuiding {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_exposure_time(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_time');
  }
  public async get_exposure_time_left(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_time_left');
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
  public async set_exposure_time(exposure_time: number) {
    return await rpcCall(this.jid, 'set_exposure_time', [exposure_time]);
  }
  public async start() {
    return await rpcCall(this.jid, 'start');
  }
  public async stop() {
    return await rpcCall(this.jid, 'stop');
  }
}

export class IAutonomous {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
  public async start() {
    return await rpcCall(this.jid, 'start');
  }
  public async stop() {
    return await rpcCall(this.jid, 'stop');
  }
}

export class IBinning {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_binning(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_binning');
  }
  public async list_binnings(): Promise<[[number, number]]> {
    return await rpcCall(this.jid, 'list_binnings');
  }
  public async set_binning(x: number, y: number) {
    return await rpcCall(this.jid, 'set_binning', [x, y]);
  }
}

export class ICalibrate {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async calibrate() {
    return await rpcCall(this.jid, 'calibrate');
  }
}

export class ICamera {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_exposure_progress(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_progress');
  }
  public async get_exposure_status(): Promise<string> {
    return await rpcCall(this.jid, 'get_exposure_status');
  }
  public async grab_data(broadcast: boolean): Promise<string> {
    return await rpcCall(this.jid, 'grab_data', [broadcast]);
  }
}

export class IConfig {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_config_caps(): Promise<{string: [boolean, boolean, boolean]}> {
    return await rpcCall(this.jid, 'get_config_caps');
  }
  public async get_config_value(name: string): Promise<any> {
    return await rpcCall(this.jid, 'get_config_value', [name]);
  }
  public async get_config_value_options(name: string): Promise<[string]> {
    return await rpcCall(this.jid, 'get_config_value_options', [name]);
  }
  public async set_config_value(name: string, value: any) {
    return await rpcCall(this.jid, 'set_config_value', [name, value]);
  }
}

export class ICooling {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_cooling(): Promise<[boolean, number, number]> {
    return await rpcCall(this.jid, 'get_cooling');
  }
  public async get_temperatures(): Promise<{string: number}> {
    return await rpcCall(this.jid, 'get_temperatures');
  }
  public async set_cooling(enabled: boolean, setpoint: number) {
    return await rpcCall(this.jid, 'set_cooling', [enabled, setpoint]);
  }
}

export class IData {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async grab_data(broadcast: boolean): Promise<string> {
    return await rpcCall(this.jid, 'grab_data', [broadcast]);
  }
}

export class IDome {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_altaz(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_altaz');
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async move_altaz(alt: number, az: number) {
    return await rpcCall(this.jid, 'move_altaz', [alt, az]);
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IExposure {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_exposure_progress(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_progress');
  }
  public async get_exposure_status(): Promise<string> {
    return await rpcCall(this.jid, 'get_exposure_status');
  }
}

export class IExposureTime {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_exposure_time(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_time');
  }
  public async get_exposure_time_left(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_time_left');
  }
  public async set_exposure_time(exposure_time: number) {
    return await rpcCall(this.jid, 'set_exposure_time', [exposure_time]);
  }
}

export class IFilters {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_filter(): Promise<string> {
    return await rpcCall(this.jid, 'get_filter');
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async list_filters(): Promise<[string]> {
    return await rpcCall(this.jid, 'list_filters');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async set_filter(filter_name: string) {
    return await rpcCall(this.jid, 'set_filter', [filter_name]);
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IFitsHeaderAfter {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_fits_header_after(namespaces: [string] | void): Promise<{string: [any, string]}> {
    return await rpcCall(this.jid, 'get_fits_header_after', [namespaces]);
  }
}

export class IFitsHeaderBefore {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_fits_header_before(namespaces: [string] | void): Promise<{string: [any, string]}> {
    return await rpcCall(this.jid, 'get_fits_header_before', [namespaces]);
  }
}

export class IFlatField {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
  public async flat_field(count: number): Promise<[number, number]> {
    return await rpcCall(this.jid, 'flat_field', [count]);
  }
}

export class IFocusModel {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_optimal_focus(): Promise<number> {
    return await rpcCall(this.jid, 'get_optimal_focus');
  }
  public async set_optimal_focus() {
    return await rpcCall(this.jid, 'set_optimal_focus');
  }
}

export class IFocuser {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_focus(): Promise<number> {
    return await rpcCall(this.jid, 'get_focus');
  }
  public async get_focus_offset(): Promise<number> {
    return await rpcCall(this.jid, 'get_focus_offset');
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async set_focus(focus: number) {
    return await rpcCall(this.jid, 'set_focus', [focus]);
  }
  public async set_focus_offset(offset: number) {
    return await rpcCall(this.jid, 'set_focus_offset', [offset]);
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IGain {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_gain(): Promise<number> {
    return await rpcCall(this.jid, 'get_gain');
  }
  public async get_offset(): Promise<number> {
    return await rpcCall(this.jid, 'get_offset');
  }
  public async set_gain(gain: number) {
    return await rpcCall(this.jid, 'set_gain', [gain]);
  }
  public async set_offset(offset: number) {
    return await rpcCall(this.jid, 'set_offset', [offset]);
  }
}

export class IImageFormat {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_image_format(): Promise<string> {
    return await rpcCall(this.jid, 'get_image_format');
  }
  public async list_image_formats(): Promise<[string]> {
    return await rpcCall(this.jid, 'list_image_formats');
  }
  public async set_image_format(fmt: string) {
    return await rpcCall(this.jid, 'set_image_format', [fmt]);
  }
}

export class IImageType {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_image_type(): Promise<string> {
    return await rpcCall(this.jid, 'get_image_type');
  }
  public async set_image_type(image_type: string) {
    return await rpcCall(this.jid, 'set_image_type', [image_type]);
  }
}

export class ILatLon {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_latlon(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_latlon');
  }
  public async move_latlon(lat: number, lon: number) {
    return await rpcCall(this.jid, 'move_latlon', [lat, lon]);
  }
}

export class IMode {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_mode(group: number): Promise<string> {
    return await rpcCall(this.jid, 'get_mode', [group]);
  }
  public async list_mode_groups(): Promise<[string]> {
    return await rpcCall(this.jid, 'list_mode_groups');
  }
  public async list_modes(group: number): Promise<[string]> {
    return await rpcCall(this.jid, 'list_modes', [group]);
  }
  public async set_mode(mode: string, group: number) {
    return await rpcCall(this.jid, 'set_mode', [mode, group]);
  }
}

export class IModule {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_error_string(): Promise<string> {
    return await rpcCall(this.jid, 'get_error_string');
  }
  public async get_label(): Promise<string> {
    return await rpcCall(this.jid, 'get_label');
  }
  public async get_state(): Promise<string> {
    return await rpcCall(this.jid, 'get_state');
  }
  public async get_version(): Promise<string> {
    return await rpcCall(this.jid, 'get_version');
  }
  public async reset_error(): Promise<boolean> {
    return await rpcCall(this.jid, 'reset_error');
  }
}

export class IMotion {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IMultiFiber {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
  public async get_fiber(): Promise<string> {
    return await rpcCall(this.jid, 'get_fiber');
  }
  public async get_fiber_count(): Promise<number> {
    return await rpcCall(this.jid, 'get_fiber_count');
  }
  public async get_pixel_position(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_pixel_position');
  }
  public async get_radius(): Promise<number> {
    return await rpcCall(this.jid, 'get_radius');
  }
  public async list_fiber_names(): Promise<[string]> {
    return await rpcCall(this.jid, 'list_fiber_names');
  }
  public async set_fiber(fiber: string) {
    return await rpcCall(this.jid, 'set_fiber', [fiber]);
  }
}

export class IOffsetsAltAz {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_offsets_altaz(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_offsets_altaz');
  }
  public async set_offsets_altaz(dalt: number, daz: number) {
    return await rpcCall(this.jid, 'set_offsets_altaz', [dalt, daz]);
  }
}

export class IOffsetsRaDec {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_offsets_radec(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_offsets_radec');
  }
  public async set_offsets_radec(dra: number, ddec: number) {
    return await rpcCall(this.jid, 'set_offsets_radec', [dra, ddec]);
  }
}

export class IPointingAltAz {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_altaz(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_altaz');
  }
  public async move_altaz(alt: number, az: number) {
    return await rpcCall(this.jid, 'move_altaz', [alt, az]);
  }
}

export class IPointingHGS {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_hgs_lon_lat(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_hgs_lon_lat');
  }
  public async move_hgs_lon_lat(lon: number, lat: number) {
    return await rpcCall(this.jid, 'move_hgs_lon_lat', [lon, lat]);
  }
}

export class IPointingHelioprojective {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_helioprojective(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_helioprojective');
  }
  public async move_helioprojective(theta_x: number, theta_y: number) {
    return await rpcCall(this.jid, 'move_helioprojective', [theta_x, theta_y]);
  }
}

export class IPointingRaDec {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_radec(): Promise<[number, number]> {
    return await rpcCall(this.jid, 'get_radec');
  }
  public async move_radec(ra: number, dec: number) {
    return await rpcCall(this.jid, 'move_radec', [ra, dec]);
  }
}

export class IPointingSeries {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async add_pointing_measure() {
    return await rpcCall(this.jid, 'add_pointing_measure');
  }
  public async start_pointing_series(): Promise<string> {
    return await rpcCall(this.jid, 'start_pointing_series');
  }
  public async stop_pointing_series() {
    return await rpcCall(this.jid, 'stop_pointing_series');
  }
}

export class IReady {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
}

export class IRoof {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IRotation {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async get_rotation(): Promise<number> {
    return await rpcCall(this.jid, 'get_rotation');
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async set_rotation(angle: number) {
    return await rpcCall(this.jid, 'set_rotation', [angle]);
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class IRunnable {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async abort() {
    return await rpcCall(this.jid, 'abort');
  }
  public async run() {
    return await rpcCall(this.jid, 'run');
  }
}

export class IRunning {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
}

export class IScriptRunner {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async run_script(script: string) {
    return await rpcCall(this.jid, 'run_script', [script]);
  }
}

export class ISpectrograph {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_exposure_progress(): Promise<number> {
    return await rpcCall(this.jid, 'get_exposure_progress');
  }
  public async get_exposure_status(): Promise<string> {
    return await rpcCall(this.jid, 'get_exposure_status');
  }
  public async grab_data(broadcast: boolean): Promise<string> {
    return await rpcCall(this.jid, 'grab_data', [broadcast]);
  }
}

export class IStartStop {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
  public async start() {
    return await rpcCall(this.jid, 'start');
  }
  public async stop() {
    return await rpcCall(this.jid, 'stop');
  }
}

export class ISyncTarget {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async sync_target() {
    return await rpcCall(this.jid, 'sync_target');
  }
}

export class ITelescope {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_motion_status(device: string | void): Promise<string> {
    return await rpcCall(this.jid, 'get_motion_status', [device]);
  }
  public async init() {
    return await rpcCall(this.jid, 'init');
  }
  public async is_ready(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_ready');
  }
  public async park() {
    return await rpcCall(this.jid, 'park');
  }
  public async stop_motion(device: string | void) {
    return await rpcCall(this.jid, 'stop_motion', [device]);
  }
}

export class ITemperatures {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_temperatures(): Promise<{string: number}> {
    return await rpcCall(this.jid, 'get_temperatures');
  }
}

export class IVideo {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_video(): Promise<string> {
    return await rpcCall(this.jid, 'get_video');
  }
  public async grab_data(broadcast: boolean): Promise<string> {
    return await rpcCall(this.jid, 'grab_data', [broadcast]);
  }
}

export class IWeather {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_current_weather(): Promise<{string: any}> {
    return await rpcCall(this.jid, 'get_current_weather');
  }
  public async get_sensor_value(station: string, sensor: string): Promise<[string, number]> {
    return await rpcCall(this.jid, 'get_sensor_value', [station, sensor]);
  }
  public async get_weather_status(): Promise<{string: any}> {
    return await rpcCall(this.jid, 'get_weather_status');
  }
  public async is_running(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_running');
  }
  public async is_weather_good(): Promise<boolean> {
    return await rpcCall(this.jid, 'is_weather_good');
  }
  public async start() {
    return await rpcCall(this.jid, 'start');
  }
  public async stop() {
    return await rpcCall(this.jid, 'stop');
  }
}

export class IWindow {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
  public async get_full_frame(): Promise<[number, number, number, number]> {
    return await rpcCall(this.jid, 'get_full_frame');
  }
  public async get_window(): Promise<[number, number, number, number]> {
    return await rpcCall(this.jid, 'get_window');
  }
  public async set_window(left: number, top: number, width: number, height: number) {
    return await rpcCall(this.jid, 'set_window', [left, top, width, height]);
  }
}

export class Interface {
  jid: string;
  constructor(jid: string) {
    this.jid = jid;
  }
}

