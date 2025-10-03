import {
    CheckCircleOutlined,
    CloseCircleOutlined,
    DownSquareFilled,
    UpSquareFilled,
  } from "@ant-design/icons";
  import Box from "@mui/material/Box";
  import Grid from "@mui/material/Grid";
  import Paper from "@mui/material/Paper";
  import Typography from "@mui/material/Typography";
  import {styled} from "@mui/material/styles";
  import {Popover, notification} from "antd";
  import React from "react";
  
  import {GalvoManualControl} from "./galvo/GalvoManualCtrl";
  
  const Item = styled(Box)(({theme}) => ({
    backgroundColor: "#fff",
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: "center",
    color: theme.palette.text.secondary,
  }));
  
  const defaultProps = {
    m: 0,
    border: 1,
  };
  
  function bit_test(num, bit) {
    return (num >> bit) % 2 !== 0;
  }
  
  function bit_set(num, bit) {
    if (bit > 30) {
      return num + -1 * (1 << bit);
    } else {
      if (num > 2147483647) {
        return num + (1 << bit);
      } else {
        return num | (1 << bit);
      }
    }
  }
  
  function bit_clear(num, bit) {
    if (num > 2147483647) {
      if (bit > 30) {
        return num + (1 << bit);
      } else {
        return num - (1 << bit);
      }
    } else {
      return num & ~(1 << bit);
    }
  }
  
  function bit_toggle(num, bit) {
    return bit_test(num, bit) ? bit_clear(num, bit) : bit_set(num, bit);
  }
  
  function ExitLed({value, info, status, onClick, ...rest}) {
    const bkColor = () => {
      if (info.fun === "NC") {
        return "white";
      }
  
      if (bit_test(status, value)) {
        return "#c7ffc7";
      } else {
        return "#f0f0f1";
      }
    };
  
    const checkClcik = e => {
      if (info.fun === "NC") {
        console.log("Clicked unsable pin");
      } else {
        onClick(e);
      }
    };
  
    let ele = <span></span>;
    if (info.io) {
      if (info.mode === "Output") {
        ele = (
          <Popover content='output' trigger='hover'>
            <UpSquareFilled
              style={{
                position: "absolute",
                right: "2px",
                top: "2px",
                color: "#08c",
              }}
            />
          </Popover>
        );
      } else {
        ele = (
          <Popover content='input' trigger='hover'>
            <DownSquareFilled
              style={{
                position: "absolute",
                right: "2px",
                top: "2px",
                color: "#08c",
              }}
            />
          </Popover>
        );
      }
    }
  
    return (
      <Grid item xs={2}>
        <Item
          onClick={checkClcik}
          sx={{backgroundColor: bkColor(), position: "relative", margin: "auto"}}>
          {ele}
          <span>
            <strong>{value}</strong>
          </span>
          <br />
          <div>
            <small>
              {info.id} {info.fun}
            </small>
          </div>
        </Item>
      </Grid>
    );
  }
  
  function ArduinoPio(props) {
    const P_GPIO = 8;
    const C_GPIO = 14;
    const C_OUT = 32;
    const C_IN = 24;
    const NUM_PINS = 32;
    var bits = 0;
  
    if (Array.isArray(props.status)) {
      bits = props.status[0];
    } else {
      bits = props.status;
    }
  
    const handle = pin => {
      props.onUpdate(pin);
    };
  
    const IoType = () => {
      if (props.name === "GPIO") {
        return "Output";
      } else if (props.name === "Outputs") {
        return "Output";
      } else {
        return "Input";
      }
    };
  
    const ArduinoInfo = pin => {
      let toRet = {
        id: "Pin",
        fun: "",
        io: false,
        mode: IoType(pin),
      };
  
      if (props.devType === "P") {
        if (props.name === "GPIO") {
          if (parseInt(pin) < P_GPIO) {
            toRet.fun = pin;
            toRet.io = true;
            return toRet;
          }
        }
      } else if (props.devType === "C") {
        if (props.name === "GPIO") {
          if (parseInt(pin) < C_GPIO) {
            toRet.fun = pin;
            toRet.io = true;
            return toRet;
          }
        } else if (props.name === "Outputs") {
          if (parseInt(pin) < C_OUT) {
            toRet.fun = pin;
            return toRet;
          }
        } else if (props.name === "Inputs") {
          if (parseInt(pin) < C_IN) {
            toRet.fun = pin;
            return toRet;
          }
        }
      }
  
      toRet.fun = "NC";
      return toRet;
    };
  
    console.log(props.name + " -> " + bits);
    return (
      <Paper elevation={2} sx={{padding: 1}}>
        <Typography variant='h5'>{props.name}</Typography>
        <Grid container spacing={0} sx={{marginTop: 1}}>
          {[...Array(NUM_PINS).keys()].map(value => {
            return (
              <ExitLed
                key={value}
                value={value}
                info={ArduinoInfo(value)}
                status={bits}
                onClick={() => {
                  if (props.interactions) {
                    handle(value);
                  }
                }}
                {...defaultProps}
              />
            );
          })}
        </Grid>
      </Paper>
    );
  }
  
  const openNotification = (title, msg, status) => {
    const color =
      status === false ? (
        <CloseCircleOutlined style={{color: "red"}} />
      ) : (
        <CheckCircleOutlined style={{color: "green"}} />
      );
  
    notification.open({
      message: title,
      description: msg,
      icon: color,
      duration: 2,
    });
  };
  
  export default class ManualControl extends React.Component {
    constructor(props) {
      super(props);
      console.log("ManualControl " + props.deviceStatus);
      this.handleClick = this.handleClick.bind(this);
      this.galvoCmd = this.galvoCmd.bind(this);
      this.checkReply = this.checkReply.bind(this);
      this.configLoopMode = this.configLoopMode.bind(this);
      this.setLoopMode = this.setLoopMode.bind(this);
      this.stopLoop = this.stopLoop.bind(this);
      this.restoreLoopMode = this.restoreLoopMode.bind(this);
  
      this.notification_title = "Manual Control";
  
      if (props.deviceStatus.deviceType === "G") {
        this.state = {
          devType: props.deviceStatus.deviceType,
          socket: props.socket,
          configuration: {},
        };
      } else if (
        props.deviceStatus.deviceType === "C" ||
        props.deviceStatus.deviceType === "P"
      ) {
        const out_masks = props.deviceStatus.out;
        const in_masks = props.deviceStatus.in;
        this.state = {
          Out: [out_masks.mask_0, out_masks.mask_1],
          In: [in_masks.mask_0, in_masks.mask_1],
          devType: props.deviceStatus.deviceType,
          socket: props.socket,
          configuration: {},
        };
      }
  
      console.log(this.state);
    }
  
    checkConnection = () => {
      if (this.state.socket.connected === false) {
        openNotification(this.notification_title, "Backend disconnected", false);
        return false;
      }
  
      return true;
    };
  
    componentDidMount() {
      this.state.socket.on("manual_command_ack", rpl => {
        this.checkReply(rpl, "manual_command_ack");
      });
      this.state.socket.on("manual_loop_cfg_ack", rpl => {
        this.checkReply(rpl, "manual_loop_cfg_ack");
      });
      this.state.socket.on("current_device_config", reply => {
        this.setState({configuration: reply});
      });
      this.state.socket.on("manual_control_status", status => {
        const out_masks = status.out;
        const in_masks = status.in;
        if (out_masks !== undefined && in_masks !== undefined) {
          this.setState({
            Out: [out_masks.mask_0, out_masks.mask_1],
            In: [in_masks.mask_0, in_masks.mask_1],
          });
        }
      });
      this.state.socket.emit("device_config");
    }
  
    componentWillUnmount() {
      this.state.socket.off("manual_command_ack");
      this.state.socket.off("manual_loop_cfg_ack");
      this.state.socket.off("current_device_config");
      this.state.socket.off("manual_control_status");
    }
  
    checkReply(reply, str) {
      if (str === "manual_command_ack") {
        this.notification_title = "Manual Control";
      } else {
        this.notification_title = "Manual Loop Control";
      }
  
      if (reply == null) {
        console.error("Empty replay");
        openNotification(
          this.notification_title,
          "No response from backend",
          false
        );
        return;
      }
      if (reply.status === "KO") {
        console.warn("Replay KO: ", reply.info);
        openNotification(this.notification_title, reply.info, false);
        return;
      }
      if (reply.status === "OK") {
        console.info(reply.info);
        openNotification(this.notification_title, reply.info, true);
      }
      this.state.socket.emit("device_info");
    }
  
    galvoCmd(value, id) {
      this.props.set_manual_info(value);
  
      if (this.props.deviceStatus.mode === "man") {
        if (this.checkConnection()) {
          this.state.socket.emit("manual_cmd", {id: id, pos: value});
        }
      } else {
        openNotification(
          this.notification_title,
          "Galvo mode must be 'Man'",
          false
        );
      }
    }
  
    handleClick(id, pin) {
      let {Out} = this.state;
      Out[id] = bit_toggle(Out[id], pin);
      console.log("pin: " + pin + " Value: " + Out[id]);
      this.state.socket.emit("manual_cmd", {gpio: Out[0], output: Out[1]});
    }
  
    configLoopMode(payload) {
      let toSend = {
        cycle_cfg: {
          address: this.props.deviceStatus.address,
          deviceType: "G",
          data: payload,
        },
      };
  
      this.state.socket.emit("config_loop_mode", toSend);
    }
  
    setLoopMode(payload) {
      let toSend = {
        cycle_cmd: {
          address: this.props.deviceStatus.address,
          deviceType: "G",
          data: payload,
        },
      };
      this.state.socket.emit("loop_mode", toSend);
    }
  
    stopLoop() {
      this.state.socket.emit("stop_loop", rpl => {
        this.checkReply(rpl, "manual_command_ack");
      });
    }
  
    restoreLoopMode() {
      this.state.socket.emit("restore_cycle_cfg");
    }
  
    render() {
      if (this.state.devType === "G") {
        return (
          <GalvoManualControl
            galvoCommand={this.galvoCmd}
            config_loop_mode={this.configLoopMode}
            loop_mode={this.setLoopMode}
            stop_loop={this.stopLoop}
            manual_info={this.props.manual_info.galvo}
            restore_loop_mode={this.restoreLoopMode}
            socket={this.state.socket}
          />
        );
      } else if (this.state.devType === "C" || this.state.devType === "P") {
        const gpio_in = this.state.In[0];
        const gpio_out = this.state.Out[0];
        const input = this.state.In[1];
        const output = this.state.Out[1];
  
        return (
          <Grid container spacing={4}>
            <Grid item xs={12}>
              <ArduinoPio
                item
                name='GPIO'
                config={this.state.configuration}
                interactions={true}
                status={[gpio_in, gpio_out]}
                devType={this.state.devType}
                onUpdate={pin => this.handleClick(0, pin)}
              />
            </Grid>
            <Grid item xs={12}>
              <ArduinoPio
                item
                name='Outputs'
                status={output}
                interactions={true}
                devType={this.state.devType}
                onUpdate={pin => this.handleClick(1, pin)}
              />
            </Grid>
            <Grid item xs={12}>
              <ArduinoPio
                item
                name='Inputs'
                status={input}
                interactions={false}
                devType={this.state.devType}
              />
            </Grid>
          </Grid>
        );
      }
      return <div></div>;
    }
  }