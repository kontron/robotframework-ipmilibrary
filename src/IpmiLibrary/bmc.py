#
# Kontron IpmiLibrary
#
# author: Michael Walle <michael.walle@kontron.com>
# author: Heiko Thiery <heiko.thiery@kontron.com>
#

class Bmc:
    def issue_bmc_cold_reset(self):
        """Sends a _bmc cold reset_ to the given controler.
        """
        self._ipmi.cold_reset()

    def get_bmc_device_id(self):
        """Sends a _bmc get device id_ command to the given controller.
        """
        device_id = self._ipmi.get_device_id()

    def product_id_should_be(self, product_id):
        """Fails if the GetDeviceID command response does not contain
        the given `device_id`.
        """
        product_id = int_any_base(product_id)
        device_id = self._ipmi.get_device_id()
        asserts.fail_unless_equal(device_id.product_id, product_id)

    def manufacturer_id_should_be(self, manufacturer_id):
        """Fails if the GetDeviceID command response does not contain
        the given `manufacturer_id`.
        """
        manufacturer_id = int_any_base(manufacturer_id)
        device_id = self._ipmi.get_device_id()
        asserts.fail_unless_equal(device_id.manufacturer_id, manufacturer_id)

    def start_watchdog_timer(self, value, action):
        """Sets and starts IPMI watchdog timer.

        The watchdog is set to `value` and after that it is started.

        The maximum value is 6553 seconds. `value` is given in Robot
        Framework's time format (e.g. 1 minute 20 seconds) that is explained in
        the User Guide.
        """

        config = pyipmi.bmc.Watchdog()
        config.timer_use = pyipmi.bmc.Watchdog.TIMER_USE_SMS_OS
        config.dont_stop = 1
        config.dont_log = 0
        config.pre_timeout_interval = 0
        config.pre_timeout_interrupt = 0
        config.timer_use_expiration_flags = 8
        # convert to 100ms
        config.initial_countdown = int(utils.timestr_to_secs(value) * 10)
        if (config.initial_countdown > 0xffff):
            raise RuntimeError('Watchdog value out of range')
        config.timeout_action = find_watchdog_action(action)
        # set watchdog
        self._ipmi.set_watchdog_timer(config)
        # start watchdog
        self._ipmi.reset_watchdog_timer()


