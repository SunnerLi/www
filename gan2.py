import tensorlayer as tl
import tensorflow as tf

def leaky_relu(x, alpha=0.2):
    return tf.maximum(tf.minimum(0.0, alpha * x), x)

class GAN(object):
    def __init__(self, filter_base, fc_unit_num, conv_depth, lambda_panelty_factor, img_depth, name=''):
        self.filter_base = filter_base
        self.fc_unit_num = fc_unit_num
        self.conv_depth = conv_depth
        self.lambda_panelty_factor = lambda_panelty_factor
        self.img_depth = img_depth
        self.name = name

    def buildPrint(self, string):
        print('-' * 100)
        print(string)
        print('-' * 100)

    def buildGraph(self, noise_ph, image_ph):
        self.img_length = image_ph.get_shape()[2]
        self.buildPrint('Build generator ...')
        self.generated_tensor = self.getGenerator(noise_ph)
        self.buildPrint('Build true discriminator ...')
        self.true_logits = self.getDiscriminator(image_ph, reuse=False)
        self.buildPrint('Build fake discriminator ...')
        self.fake_logits = self.getDiscriminator(self.generated_tensor, reuse=True)

    def getDiscriminator(self, img_ph, reuse=False):
        with tf.variable_scope(self.name + 'discriminator', reuse=reuse):
            tl.layers.set_name_reuse(reuse)
            network = tl.layers.InputLayer(img_ph, name ='discriminator_input_layer')
            network = tl.layers.ReshapeLayer(network, [tf.shape(img_ph)[0], self.img_height, self.img_width, self.img_depth], name ='discriminator_reshape_layer')
            for i in range(self.conv_depth):
                network = tl.layers.Conv2d(network, n_filter = self.filter_base, name ='discriminator_conv2d_%s'%str(i))
                network = tl.layers.BatchNormLayer(network, act = leaky_relu, name ='discriminator_batchnorm_layer_%s'%str(i))
                network = tl.layers.MaxPool2d(network, name='discriminator_maxpool_%s'%str(i))
            network = tl.layers.FlattenLayer(network)
            network = tl.layers.DenseLayer(network, n_units = self.fc_unit_num, act = tf.nn.relu, name ='discriminator_dense_layer')
            network = tl.layers.DenseLayer(network, n_units = 1)
            return network.outputs

    def getGenerator(self, noise_ph):
        dense_recover_length = self.img_length // (2 ** self.conv_depth)
        if dense_recover_length * (2 ** self.conv_depth) != self.img_length:
            raise Exception('Invalid image length...')
        with tf.variable_scope(self.name + 'generator'):
            network = tl.layers.InputLayer(noise_ph)
            network = tl.layers.DenseLayer(network, n_units = self.fc_unit_num, name ='generator_dense_layer_1')
            network = tl.layers.BatchNormLayer(network, act = tf.nn.relu, name ='generator_batchnorm_layer_1')
            network = tl.layers.DenseLayer(network, n_units = dense_recover_length * dense_recover_length * self.filter_base * (2  ** (self.conv_depth - 1)), name ='generator_dense_layer_2')
            network = tl.layers.ReshapeLayer(network, tf.stack([tf.shape(noise_ph)[0], dense_recover_length, dense_recover_length, self.filter_base * (2  ** (self.conv_depth - 1))]))
            network = tl.layers.BatchNormLayer(network, act = tf.nn.relu, name ='generator_batchnorm_layer_2')
            print(network.outputs.get_shape())
            for i in range(self.conv_depth, 1, -1):
                height = dense_recover_length * (2 ** (self.conv_depth - i + 1))
                width  = dense_recover_length * (2 ** (self.conv_depth - i + 1))
                channel = self.filter_base * (2  ** (i - 1))
                network = tl.layers.DeConv2d(network, n_out_channel = channel, strides = (2, 2), out_size = (height, width), name ='generator_decnn2d_%s'%str(1+i*2))
                network = tl.layers.BatchNormLayer(network, act = tf.nn.sigmoid, name ='generator_batchnorm_layer_%s'%str(self.conv_depth-i+3))
                print('!')
            network = tl.layers.DeConv2d(network, n_out_channel = self.img_depth, strides = (2, 2), out_size = (self.img_height, self.img_width), name ='generator_decnn2d_final')
            network = tl.layers.ReshapeLayer(network, [tf.shape(noise_ph)[0], self.img_height, self.img_width, self.img_depth], name ='generator_reshape_layer')
            return network.outputs