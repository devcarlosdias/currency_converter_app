import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';
import 'package:dartz/dartz.dart';

abstract class SupportedRepository {
  Future<Either<Exception, List<SupportedCurrency>>> getSupportedCurrency();
}

