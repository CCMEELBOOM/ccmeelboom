# Hydrophone DAC HAT README

This document explains the theory and the script used to read hydrophone data from two MCC 172 DAC HAT boards mounted on the BlueROV2. The document covers the conversion of voltage readings into pressure and sending sound pressure level values to a PC over a socket connection as well as the derivation of the hydrophone sensitivity.

---

## Sensitivity Theory

A hydrophone converts underwater pressure changes into a voltage signal. The relationship between voltage, pressure, and hydrophone sensitivity is:

$$
S = \frac{V}{P}
$$

where $S$ is the hydrophone sensitivity in $V/Pa$, $V$ is the measured voltage, and $P$ is acoustic pressure in pascals. Rearranging gives:

$$
P = \frac{V}{S}
$$


The original hydrophone sensitivity is $-211 \; dB$ $\ re$ $\ 1V/\mu Pa$. With the preamp gain of $+26 \ dB$, the total sensitivity becomes:

$$
S_{dB} = -211 + 26 = -185 \; dB \; re \; 1V/\mu Pa
$$

Converting this to a linear value:

$$
S_{dB} = 20log_{10}(\frac{S_{linear}}{1V/\mu Pa})
$$

$$
S_{linear} = 10^{S_{dB}/20}
$$

$$
S_{linear} = 10^{-185/20} = 5.6234 \times 10^{-10} \ \frac{V}{\mu Pa}
$$

Since $1 \ Pa = 10^6 \ \mu Pa$:

$$
S = 5.6234 \times 10^{-10} \times 10^6 = 5.6234 \times 10^{-4} \ \frac{V}{Pa}
$$

---

## RMS Pressure Calculation

The hydrophone signal is noisy and changes over time, so the script does not use only one sample. Instead, it reads a group of samples and calculates the RMS value.

$$
P_{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^{N}P_i^2}
$$

where $N$ is the number of samples and $P_i$ is each pressure value.

The script first converts each voltage sample into pressure:

$$
P_i = \frac{V_i}{S}
$$

Then it calculates the RMS pressure for each hydrophone channel.

---

## Converting Pressure to Decibels

After RMS pressure is calculated, it is converted into underwater sound pressure level using the underwater reference pressure of $1 \ \mu Pa$.

$$
dB = 20 \log_{10}\left(\frac{P_{RMS}}{P_{ref}}\right)
$$

where:

$$
P_{ref} = 1 \times 10^{-6} \ Pa
$$

So the equation used by the script is:

$$
dB = 20 \log_{10}\left(\frac{P_{RMS}}{1 \times 10^{-6}}\right)
$$

A very small lower limit is used in the code to avoid taking the logarithm of zero.

---



## How the Script Works

The script reads hydrophone data from two MCC 172 boards. Board 0 uses one channel, and Board 1 uses two channels. This gives three hydrophone channels total.

The main configuration values are:

| Variable | Purpose |
|---|---|
| `PC_IP` | IP address of the PC receiving the data |
| `PC_PORT` | Socket port used to send data |
| `SAMPLE_RATE` | MCC 172 sampling rate, set to `25000 Hz` |
| `SAMPLES_PER_READ` | Number of samples processed at once, set to `50` |
| `sensitivity_mV_per_Pa` | Hydrophone sensitivity in `mV/Pa` |

The script follows this process:

1. Connect to the two MCC 172 boards.
2. Enable IEPE power for the hydrophone channels.
3. Start continuous analog input scanning.
4. Connect to the PC using a TCP socket.
5. Read voltage samples from all three hydrophones.
6. Convert voltage samples to pressure values.
7. Calculate RMS pressure for each channel.
8. Convert RMS pressure to decibels.
9. Send the three dB values to the PC as one comma-separated line.

The output sent to the PC is a list:

```TEXT
hydrophone_0_dB,hydrophone_1_dB,hydrophone_2_dB
```

Example:

```TEXT
132.4,128.9,130.1
```

---

## Appendix 
[Teledyne Marine TC4013 Specifications](https://www.teledynemarine.com/en-us/products/SiteAssets/RESON/TC4013%20product%20leaflet.pdf?) 

[Aquarian Audio IEPE1 IEPE-Powered Hydrophone Preamp](https://www.aquarianaudio.com/iepe1.html)