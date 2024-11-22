if ([:len [/user find name="ROS7-user"]] = 0) do={
  :put "Adding user ROS7-user"
  /user add name=ROS7-user group=full password=vagrant
}

