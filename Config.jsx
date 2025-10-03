import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  DownloadOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import {Button, Divider, notification} from "antd";
import React, {useEffect, useState} from "react";
import ReactJson from "react-json-view";

import "./Config.scss";

export default function Config(props) {
  const [filedownloadlink, setFiledownloadlink] = useState("");

  const currentConfig = props.configuration;
  const setConfiguration = props.set_configuration;

  const handleSomeEvent = () => {
    var myURL = window.URL || window.webkitURL; //window.webkitURL works in Chrome and window.URL works in Firefox
    var blob = new Blob([JSON.stringify(currentConfig)], {
      type: "application/json",
    });
    var jsonUrl = myURL.createObjectURL(blob);
    setFiledownloadlink(jsonUrl);
  };

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

  useEffect(
    () => {
      props.socket.on("current_device_config", reply => {
        console.log("Device Update Config");
        setConfiguration(reply);
      });

      props.socket.emit("device_config");
    },
    [props.config, props.socket, setConfiguration],
    () => {}
  );

  function onSubmit() {
    console.log(currentConfig); //TOREM
    props.socket.emit("apply_config", currentConfig);
  }

  function onSave() {
    props.socket.emit("save_template", currentConfig, result => {
      if (result == null) {
        openNotification(
          "Save Template Parameters",
          "No response from backend",
          false
        );
        return;
      }

      if (result.status === "OK") {
        openNotification("Save Template Parameters", "Succeed", true);
      } else {
        openNotification("Save Template Parameters", result.info, false);
      }
    });
  }

  function onLoad() {
    props.socket.emit("load_template", result => {
      if (result == null) {
        openNotification(
          "Load Template Parameters",
          "No response from backend",
          false
        );
      } else {
        setConfiguration(result);
        openNotification("Load Template Parameters", "Succeed", true);
      }
    });
  }

  const onJsonEdit = edit => {
    console.log(edit.updated_src); //TOREM
    setConfiguration(edit.updated_src);
  };

  const onInputClick = event => {
    event.target.value = "";
  };

  const onUploadClick = e => {
    console.log(e.target.files[0]);
    var reader = new FileReader();
    reader.readAsText(e.target.files[0], "UTF-8");
    reader.onload = function (evt) {
      console.log(evt.target.result);
      setConfiguration(JSON.parse(evt.target.result));
    };
    reader.onerror = function (evt) {
      console.error("Error");
      openNotification("File Reader", "Error reading file from disk", false);
    };
  };

  return (
    <React.Fragment>
      <div style={{margin: "10px"}}>
        <ReactJson
          src={currentConfig}
          onEdit={edit => onJsonEdit(edit)}
          onAdd={add => onJsonEdit(add)}
          onDelete={edit => onJsonEdit(edit)}
        />
      </div>
      <Divider />
      <Button block type='primary' onClick={onSubmit} style={{margin: "5px"}}>
        {" "}
        Submit{" "}
      </Button>
      <Button block onClick={onLoad} style={{margin: "5px"}}>
        {" "}
        Load as Template{" "}
      </Button>
      <Button block onClick={onSave} style={{margin: "5px"}}>
        {" "}
        Save as Template{" "}
      </Button>
      <label className='ant-btn ant-btn-block' style={{margin: "5px"}}>
        <input type='file' onClick={onInputClick} onInput={onUploadClick} />
        <UploadOutlined />
        <span>Upload Configuration</span>
      </label>

      <a download='DeviceConfigurationExport.json' href={filedownloadlink}>
        <Button style={{margin: "5px"}} block onClick={handleSomeEvent}>
          <DownloadOutlined />
          Download Configuration
        </Button>
      </a>
    </React.Fragment>
  );
}